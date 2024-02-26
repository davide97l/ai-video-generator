"""$
{
    "name": "generateVoiceVits",
    "displayName": "",
    "description": "A Python method that downloads a specified wav file, clones the voice, generates a new speech - potentially in another language - from provided text, and subsequently uploads the newly created wav file to AWS, finally returning the URL of the uploaded file.",
    "inputPattern": {
        "type": "object",
        "required": [
            "voice",
            "audio_url"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": "Voice to use to generate new audio"
            },
            "audio_url": {
                "type": "string",
                "description": "URL of the audio to be cloned"
            },
            "clean_noise": {
                "type": "boolean",
                "description": "Clean audio input noise"
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
                "description": "Url of the wav audio file"
            }
        }
    },
    "tag": "VoiceCloning",
    "testCases": [
        {
            "voice": "chinese_poadcast_woman1",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/voice/zh_woman1_split.wav",
            "clean_noise": true
        },
        {
            "voice": "",
            "audio_url": "",
            "clean_noise": false
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
    audio_url = event.get('audio_url')
    voice= event.get('voice')
    clean_noise = event.get('clean_noise')
    api_ip = os.environ.get('api_ip')

    voice_clone_url = f"http://{api_ip}:5001/generate_voice/"

    data = {
        "audio_url": audio_url,
        "voice": voice,
        "clean_noise": clean_noise
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print('Generating voice...')
    response = requests.post(voice_clone_url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f'Voice cloning failed with status code: {response.status_code}')
    print('Voice generated')

    audio_path = voice + '_' + audio_url.split('/')[-1]
    # Save the file to the directory
    with open(audio_path, 'wb') as file:
        file.write(response.content)

    result_url = upload_to_aws(audio_path)

    # clean up
    os.remove(audio_path)

    return {
        "audio_url": result_url
    }

        