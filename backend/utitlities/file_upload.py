import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv  

load_dotenv() 

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_to_cloudinary(file_bytes: bytes, mime_type: str) -> str:
    """Upload any file, get back a public URL."""
    resource_type = "video" if mime_type.startswith("video") else "audio" if mime_type.startswith("audio") else "image"
    result = cloudinary.uploader.upload(
        file_bytes,
        resource_type=resource_type,
        folder="echopersona"
    )
    return result["secure_url"]