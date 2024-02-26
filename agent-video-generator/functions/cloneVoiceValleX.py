"""$
{
    "name": "cloneVoiceValleX",
    "displayName": "",
    "description": "This Python method downloads a wav file, replicates the voice, generates speech from provided text (potentially in a different language), uploads the new file to AWS, and returns the URL.\n\n- The input wav file of the speaker to be cloned MUST be < 15s\n- For now only English to Chinese is supported",
    "inputPattern": {
        "type": "object",
        "required": [
            "text"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text from which to generate the new voice"
            },
            "audio_url": {
                "type": "string",
                "description": "The url for the original audio file that needs to be processed"
            },
            "transcript": {
                "type": "string",
                "description": ""
            },
            "character_name": {
                "type": "string",
                "description": "Name of the character (optional)"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "audio_url"
        ],
        "properties": {
            "audio_url": {
                "type": "string",
                "description": "The URL of the audio file uploaded to AWS"
            }
        }
    },
    "tag": "VoiceCloning",
    "testCases": [
        {
            "text": "今天阳光明媚，温度很适宜，所以我打算去附近的公园漫步、欣赏风景、放松心情",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/voice/davide1_split.wav",
            "transcript": "",
            "character_name": "tony_stark"
        },
        {
            "text": "I think I is going to rule the earth one day, but fortunately this day is still very far.",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/tony_stark.wav",
            "transcript": "",
            "character_name": "tony_stark"
        },
        {
            "text": "I think I is going to rule the earth one day, 但是那天还没到",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/tony_stark.wav",
            "transcript": "",
            "character_name": "tony_stark"
        }
    ],
    "aiPrompt": "Given the url of a wav file and a text. Download the file, clone the voice and generate a speech according to the next text, the new text can also be in a different language. Upload the new generated wav file to aws and return the url",
    "greeting": ""
}
$"""

import os
import json
import boto3
import requests
import random
import string

s3 = boto3.resource('s3')

def download_file(url: str, save_path: str):
    resp = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(resp.content)


def generate_random_string(length):
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def upload_to_aws(filename: str) -> str:
    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    s3_client = session.client('s3')
    bucket_path = 'voice-clone'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    return url


def mindsflow_function(event, context) -> dict:
    # get from event
    audio_url = event.get('audio_url', None)
    text = event.get('text')
    character_name = event.get('character_name', None)
    transcript = event.get('transcript', None)
    api_ip = os.environ.get('api_ip')

    if character_name is None or len(character_name) == 0:
        character_name = 'temp'+generate_random_string(10)
    
    if transcript is not None and len(transcript) == 0:
        transcript = None

    voice_clone_url = f"http://{api_ip}:5000/voice_clone/"

    data = {
        "audio_url": audio_url,
        "character_name": character_name,
        "transcript": transcript
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print('Cloning voice...')
    response = requests.post(voice_clone_url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f'Voice cloning failed with status code: {response.status_code}')
    print('Voice cloned')

    voice_gen_url = f"http://{api_ip}:5001/generate_audio/"

    data = {
        'character_name': character_name,
        'text': text
    }

    print('Generating new voice...')
    response = requests.post(voice_gen_url, json=data)
    if response.status_code != 200:
        raise RuntimeError(f'Voice generation failed with status code: {response.status_code}')
    print('New voice generated')

    audio_path = audio_url.split('/')[-1]
    # Save the file to the directory
    with open(audio_path, 'wb') as file:
        file.write(response.content)

    result_url = upload_to_aws(audio_path)

    # clean up
    os.remove(audio_path)

    return {
        "audio_url": result_url
    }

        