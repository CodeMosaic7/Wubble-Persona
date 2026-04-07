import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

def get_response(req_id, max_retries=40, interval=30):
    headers = {"authorization": f"Bearer {os.getenv('WUBBLE_API_KEY')}"}
    url = f"https://api.wubble.ai/api/v1/request/{req_id}/status"
    completed_url=f"https://api.wubble.ai/api/v1/polling/{req_id}"
    for attempt in range(max_retries):
        time.sleep(interval)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Attempt {attempt + 1}: HTTP {response.status_code}, retrying...")
            continue
        data = response.json()
        status = data.get("status")
        if status == "completed":
            print("Response ready:", data)
            response = requests.get(completed_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching completed response: {response.status_code}")
                return None
        print(f"Attempt {attempt + 1}: status='{status}', retrying in {interval}s...")

    raise TimeoutError(f"Response not ready after {max_retries} retries")