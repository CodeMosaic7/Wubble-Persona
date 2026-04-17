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
from Video_generator.video_engine import create_video
from utitlities.beat_sync import create_beat_synced_video
from wubble.get_response import get_response
from pathlib import Path
from components.parsing import parse_wubble_response, build_lyrics_subtitles


load_dotenv()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

RESOLUTION_MAP = {
    "reels": "1080x1920",
    "tiktok": "1080x1920",
    "shorts": "1080x1920",
    "square": "1080x1080",
    "landscape": "1920x1080",
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


@app.post("/upload") #uploads + generates audio/music
async def upload_file(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    mime = file.content_type
    if mime is None:
        raise HTTPException(status_code=400, detail="Invalid file type")
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
    platform: str = Form("reels"), # type of video
    audio_url: str = Form(...),   # link of video       
    media: UploadFile = File(...), #images and videos
):
    # Validate inputs
    if not media:
        raise HTTPException(status_code=400, detail="Please upload at least one image or video")

    if not audio_url.startswith("http"):
        raise HTTPException(status_code=400, detail="audio_url must be a valid HTTP/HTTPS URL")

    allowed_types = ("image/", "video/")
    if media.content_type is not None:
        if not any(media.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(status_code=400, detail=f"{media.filename} must be an image or video")

    resolution = RESOLUTION_MAP.get(platform, "1080x1920")
    job_id = audio_url.split("/")[-2]     # extracts "38181783-11d7-4855-94f9-d50205e0f61c"
    audio_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp3")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(audio_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Failed to download audio (HTTP {resp.status_code})")
        with open(audio_path, "wb") as f:
            f.write(resp.content)
    
    # Save uploaded media 
    media_paths = []
    media_dest = os.path.join(UPLOAD_DIR, media.filename)
    with open(media_dest, "wb") as f:
        shutil.copyfileobj(media.file, f)
    media_paths = [media_dest]
    final_output = os.path.join(OUTPUT_DIR, f"{job_id}_{platform}.mp4")

    try:
        create_video(
            media_paths=media_paths,
            audio_path=audio_path,
            output_path=final_output,
            resolution=resolution,
            platform=platform,
            use_llm=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")

    # Cleanup 
    for path in media_paths:
        try: os.remove(path)
        except Exception: pass
    try: os.remove(audio_path)
    except Exception: pass

    return FileResponse(
        path=final_output,
        media_type="video/mp4",
        filename=f"persona_{platform}.mp4",
    )

