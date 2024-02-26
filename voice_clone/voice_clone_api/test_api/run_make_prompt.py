import requests
import json

# Specify the API endpoint
url = "http://IP/voice_clone/"

# Specify the data payload
data = {
    "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/tony_stark.wav",
    "character_name": "xxx"
}

headers = {
    'Content-Type': 'application/json'
}

response = requests.post(url, data=json.dumps(data), headers=headers)

if response.status_code == 200:
    print(f"Response from server: {response.json()}")
else:
    print(f"Failed to get response. Status code: {response.status_code}")