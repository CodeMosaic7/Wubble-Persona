import requests
import os
from dotenv import load_dotenv
from .get_response import get_response

load_dotenv()

ENDPOINT = "https://api.wubble.ai/api/v1/chat"
def chat_with_wubble(prompt=None, images=None, audios=None, videos=None):
    if not prompt or prompt == "None":
        return {"message": "Provide a prompt to chat with Wubble and generate customized music."}
    payload = {
        "prompt": prompt,
        "images": images or [],
        "audios": audios or [],
        "videos": videos or [],
        "vo": True,
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('WUBBLE_API_KEY')}",
        "Content-Type": "application/json",
    }
    confirmation = requests.post(ENDPOINT, headers=headers, json=payload)
    confirmation.raise_for_status()
    req_id = confirmation.json().get("request_id")
    if not req_id:
        raise ValueError("No request_id returned from Wubble")
    print(f"🎵 Wubble request_id: {req_id}")
    song_data = get_response(req_id)
    return song_data    