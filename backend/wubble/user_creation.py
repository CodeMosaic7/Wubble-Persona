import requests

url = "https://api.wubble.ai/api/user"
def user_validation(email,plan):
    if not email:
        return False, "Email is required."
    
    if not plan:
        return False, "Plan is required."
    
    payload = {
    "email": email,
    "plan": plan
    }
    headers = {"content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.status_code == 200, response.text
if __name__ == "__main__":
    email = "msmanika763348@gmail.com"
    plan = "free"
    is_valid, message = user_validation(email, plan)
    print(message)