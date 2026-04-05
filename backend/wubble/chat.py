import requests
import os
from dotenv import load_dotenv
from .get_response import get_response

load_dotenv()

endpoint="https://api.wubble.ai/api/v1/chat" #
def chat_with_wubble(prompt=None, images=None, audios=None, videos=None):
    if prompt=="None":
        return {"message": "Provide a prompt to chat with Wubble and generate customized music."}
    payload = {
        "prompt": prompt,
        "images": images,
        "audios": audios,
        "videos": videos,
        "vo": True
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('WUBBLE_API_KEY')}",
        "Content-Type": "application/json"
    }
    get_confirmation = requests.post(endpoint, headers=headers, json=payload)
    print(get_confirmation.json().get("request_id"))
    get_song=get_response(get_confirmation.json().get("request_id"))

    return get_song
