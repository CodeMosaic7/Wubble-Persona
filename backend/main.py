import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utitlities.file_upload import upload_to_cloudinary
from wubble.user_creation import user_validation
from wubble.chat import chat_with_wubble

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Persona")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    mime = file.content_type

    if not mime.startswith(("image", "video", "audio")):
        raise HTTPException(status_code=400, detail="Only image/video/audio allowed")

    file_bytes = await file.read()
    media_url = upload_to_cloudinary(file_bytes, mime)
    print(media_url)
    images  = [media_url] if mime.startswith("image") else []
    videos  = [media_url] if mime.startswith("video") else []
    audios  = [media_url] if mime.startswith("audio") else []

    response = chat_with_wubble(prompt=prompt, images=images, videos=videos, audios=audios)
    print(response)
    return response


@app.post("/login")
async def validate_user(email:str,plan:str):
    is_valid, message = user_validation(email, plan)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return {"message": "User validated successfully", "email": email, "plan": plan}


