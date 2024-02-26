import os
import json
import boto3
import requests
import random
import string

default_train_config = 'config_1000'

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
