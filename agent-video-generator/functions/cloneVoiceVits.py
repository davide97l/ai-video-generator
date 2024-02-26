"""$
{
    "name": "cloneVoiceVits",
    "displayName": "",
    "description": "The Python method is designed to download a WAV file from a specified URL, clone the voice from the file, and generate new speech from a supplied text (potentially in another language). The newly created WAV file is then uploaded to AWS and the URL",
    "inputPattern": {
        "type": "object",
        "required": [
            "dataset_url"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": "Name of the cloned voice"
            },
            "audio_split": {
                "type": "integer",
                "description": ""
            },
            "clean_noise": {
                "type": "boolean",
                "description": "Clean noise in audio for training"
            },
            "dataset_url": {
                "type": "string",
                "description": "The url of the original wav file"
            },
            "train_config": {
                "type": "string",
                "description": "The new text to generate speech"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "voice",
            "succeeded"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": ""
            },
            "succeeded": {
                "type": "boolean",
                "description": ""
            }
        }
    },
    "tag": "VoiceCloning",
    "testCases": [
        {
            "voice": "",
            "audio_split": 12,
            "clean_noise": true,
            "dataset_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/chinese_poadcast_woman1.zip",
            "train_config": "config_1000"
        },
        {
            "voice": "",
            "audio_split": 0,
            "clean_noise": false,
            "dataset_url": "",
            "train_config": ""
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

default_train_config =  'config_1000'

def mindsflow_function(event, context) -> dict:
    # get from event
    dataset_url = event.get('dataset_url')
    config = event.get('train_config', default_train_config)
    split = event.get('audio_split', 12)
    clean_noise = event.get('clean_noise', False)
    voice = event.get('voice', None)
    api_ip = os.environ.get('api_ip')

    if config is None or len(config) == 0:
        config = default_train_config
    if voice is not None and len(voice) == 0:
        voice = None

    voice_clone_url = f"http://{api_ip}:5000/voice_clone/"

    data = {
        "dataset_url": dataset_url,
        "config": config,
        "split": split,
        "clean_noise": clean_noise
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print('Cloning voice...')
    response = requests.post(voice_clone_url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f'Voice cloning failed with status code: {response.status_code}')
    print('Voice cloned')

    response_dict = response.json()

    return {
        "succeeded": response_dict["succeeded"],
        "voice": response_dict["voice"] if voice is None else voice
    }

        