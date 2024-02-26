"""$
{
    "name": "splitVoiceMusic",
    "displayName": "",
    "description": "This Python method downloads an audio file from a given URL, separates music and voice using Spleeter, uploads the results to S3, and returns their URLs.",
    "inputPattern": {
        "type": "object",
        "required": [
            "audio_url"
        ],
        "properties": {
            "audio_url": {
                "type": "string",
                "description": "The url of the audio file to be processed"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "vocals_url",
            "accompaniment_url"
        ],
        "properties": {
            "vocals_url": {
                "type": "string",
                "description": "The url of the vocal part of the audio file on S3"
            },
            "accompaniment_url": {
                "type": "string",
                "description": "The url of the accompaniment part of the audio file on S3"
            }
        }
    },
    "tag": "DataPreprocessing",
    "testCases": [
        {
            "audio_url": "https://github.com/deezer/spleeter/raw/master/audio_example.mp3"
        },
        {
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/dd6f9f73-de0c-4792-a48c-ccc2e8abe7bd_audio.wav"
        }
    ],
    "aiPrompt": "Given the url of a audio file, download it. split music and voice with Spleeter. Upload the results to s3 and return their urls",
    "greeting": ""
}
$"""

import json
import os
import subprocess
import urllib.request
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import shutil


def download_file(url: str) -> str:
    local_filename = url.split('/')[-1]
    urllib.request.urlretrieve(url, local_filename)
    return local_filename

def upload_to_aws(filename: str) -> str:
    # Uses your AWS credentials to access the service
    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')
    # Create a session using the provided credentials
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    # Create an S3 client
    s3_client = session.client('s3')
    bucket_path = 'ai-video'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    return url

def mindsflow_function(event, context) -> dict:

    # execute only first time to set up env
    def execute_command(command):
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    execute_command("pip uninstall -y ffmpeg")
    execute_command("pip uninstall -y ffmpeg-python")
    execute_command("pip install ffmpeg-python")
    execute_command("pip install spleeter")

    from spleeter.separator import Separator
    
    # Get the audio URL from the event
    audio_url = event.get("audio_url")
    
    # Download the audio file
    audio_file = download_file(audio_url)
    audio_name = audio_file.split('.')[0]

    # Split the music and voice with Spleeter
    vocals_file = f"{audio_name}/vocals.wav"
    accompaniment_file = f"{audio_name}/accompaniment.wav"


    # Create a separator object
    separator = Separator('spleeter:2stems')

    # Use the separator to separate the streams
    # 'audio_example.mp3' is your input audio file
    separator.separate_to_file(audio_file, '')
    
    # Upload the results to S3
    vocals_url = upload_to_aws(vocals_file)
    accompaniment_url = upload_to_aws(accompaniment_file)

    execute_command("pip uninstall spleeter")
    
    # Define result
    result = {
        'vocals_url': vocals_url,
        'accompaniment_url': accompaniment_url
    }

    # Delete the files after uploading
    os.remove(vocals_file)
    os.remove(accompaniment_file)
    shutil.rmtree(audio_name)

    return result
        