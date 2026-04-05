import requests
import time
import os
from dotenv import load_dotenv
load_dotenv()


def get_response(req_id, max_retries=40, interval=30):
    headers = {"authorization": f"Bearer {os.getenv('WUBBLE_API_KEY')}"}
    url = f"https://api.wubble.ai/api/v1/request/{req_id}/status"

    for attempt in range(max_retries):
        time.sleep(interval)
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("status") == "completed":
            print("Response ready:", data)
            return data
        print(f"Attempt {attempt + 1}: still processing... retrying in {interval}s")
    
    raise TimeoutError(f"Response not ready after {max_retries} retries")