import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
from dotenv import load_dotenv
import httpx
from utitlities.file_upload import upload_to_cloudinary
from wubble.user_creation import user_validation
from wubble.chat import chat_with_wubble
from utitlities.video import create_video
from utitlities.beat_sync import create_beat_synced_video

load_dotenv()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

RESOLUTION_MAP = {
    "reels":   "1080x1920",   
    "youtube": "1920x1080",  
    "square":  "1080x1080",  
}

app = FastAPI(title="Persona")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/login")
async def validate_user(email: str, plan: str):
    is_valid, message = user_validation(email, plan)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return {"message": "User validated successfully", "email": email, "plan": plan}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    mime = file.content_type
    if not mime.startswith(("image", "video", "audio")):
        raise HTTPException(status_code=400, detail="Only image/video/audio files allowed")

    file_bytes = await file.read()
    media_url = upload_to_cloudinary(file_bytes, mime)

    images = [media_url] if mime.startswith("image") else []
    videos = [media_url] if mime.startswith("video") else []
    audios = [media_url] if mime.startswith("audio") else []

    song_data = chat_with_wubble(prompt=prompt, images=images, videos=videos, audios=audios)
    return song_data


@app.post("/generate-video")
async def generate_video(
    req_id: str = Form(...),
    platform: str = Form("reels"),
    media: Optional[List[UploadFile]] = File(None),   # images + videos together
):
    # Validate inputs
    if not media or len(media) == 0:
        raise HTTPException(status_code=400, detail="Please upload at least one image or video")

    allowed_types = ("image/", "video/")
    for m in media:
        if not any(m.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(status_code=400, detail=f"{m.filename} must be an image or video")

    resolution = RESOLUTION_MAP.get(platform, "1080x1920")

    # Save uploaded media locally
    media_paths = []
    for m in media:
        dest = os.path.join(UPLOAD_DIR, m.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(m.file, f)
        media_paths.append(dest)

    # Fetch song from Wubble using req_id
    from wubble.get_response import get_response
    try:
        song_data = get_response(req_id)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Song not ready yet. Try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch song: {str(e)}")

    # Download the audio file locally
    audio_url = song_data.get("result", {}).get("audio_url")  # adjust key per Wubble response
    if not audio_url:
        raise HTTPException(status_code=500, detail="No audio URL in Wubble response")

    import httpx
    audio_path = os.path.join(OUTPUT_DIR, f"{req_id}.mp3")
    async with httpx.AsyncClient() as client:
        audio_resp = await client.get(audio_url)
        with open(audio_path, "wb") as f:
            f.write(audio_resp.content)

    # -- Create video with LLM-planned edit --
    output_path = os.path.join(OUTPUT_DIR, f"{req_id}_{platform}.mp4")
    try:
        create_video(
            media_paths=media_paths,
            audio_path=audio_path,
            output_path=output_path,
            resolution=resolution,
            platform=platform,
            use_llm=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")

    for path in media_paths:
        try:
            os.remove(path)
        except Exception:
            pass

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"persona_{platform}.mp4",
    )

@app.post("/generate-video/beat-sync")
async def generate_beat_sync_video(
    req_id: str = Form(...),
    platform: str = Form("reels"),
    media: Optional[List[UploadFile]] = File(None),
):
    if not media or len(media) == 0:
        raise HTTPException(status_code=400, detail="Upload at least one image or video")

    for m in media:
        if not any(m.content_type.startswith(t) for t in ("image/", "video/")):
            raise HTTPException(status_code=400, detail=f"{m.filename} must be image or video")

    resolution = RESOLUTION_MAP.get(platform, "1080x1920")

    # Save media
    media_paths = []
    for m in media:
        dest = os.path.join(UPLOAD_DIR, m.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(m.file, f)
        media_paths.append(dest)

    # Fetch song
    from wubble.get_response import get_response
    try:
        song_data = get_response(req_id)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Song not ready yet")

    audio_url = song_data.get("result", {}).get("audio_url")
    if not audio_url:
        raise HTTPException(status_code=500, detail="No audio URL in Wubble response")

    audio_path = os.path.join(OUTPUT_DIR, f"{req_id}.mp3")
    async with httpx.AsyncClient() as client:
        audio_resp = await client.get(audio_url)
        with open(audio_path, "wb") as f:
            f.write(audio_resp.content)

    output_path = os.path.join(OUTPUT_DIR, f"{req_id}_{platform}_beatsync.mp4")

    try:
        from utilities.beat_sync import create_beat_synced_video
        result = create_beat_synced_video(
            media_paths=media_paths,
            audio_path=audio_path,
            output_path=output_path,
            resolution=resolution,
            platform=platform,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beat sync failed: {str(e)}")

    # Cleanup
    for path in media_paths:
        try: os.remove(path)
        except: pass

    # Return video + metadata in headers
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"beatsync_{platform}.mp4",
        headers={
            "X-BPM": str(result["bpm"]),
            "X-Total-Cuts": str(result["total_cuts"]),
            "X-Audio-Duration": str(result["audio_duration"]),
        }
    )