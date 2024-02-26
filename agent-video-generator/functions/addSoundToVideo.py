"""$
{
    "name": "addSoundToVideo",
    "displayName": "",
    "description": "The method is designed to add sound to a video file.",
    "inputPattern": {
        "type": "object",
        "required": [
            "audio_url",
            "video_url"
        ],
        "properties": {
            "volume": {
                "type": "number",
                "description": ""
            },
            "audio_url": {
                "type": "string",
                "description": "URL of the audio to be downloaded"
            },
            "video_url": {
                "type": "string",
                "description": "URL of the video to be downloaded"
            },
            "repeat_audio": {
                "type": "boolean",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "video_url"
        ],
        "properties": {
            "video_url": {
                "type": "string",
                "description": "The URL of the video file with background music added and uploaded to S3"
            }
        }
    },
    "tag": "DataPreprocessing",
    "testCases": [
        {
            "volume": 0.5,
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/7d670407-7729-4db1-b468-6ca545051de5_audio/accompaniment.wav",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/combine_e37e383a-00db-46d9-a5fa-d9dbfa5e760c.mp4",
            "repeat_audio": false
        }
    ],
    "aiPrompt": "addSoundToVideo",
    "greeting": ""
}
$"""

import json
import requests
import moviepy.editor as mpy
import boto3
import time
import random
import string
import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np
from moviepy.audio.fx.all import volumex

def download_file(url: str, save_as: str) -> None:
    response = requests.get(url, stream=True)
    with open(save_as, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def get_random_string():
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for _ in range(8))
    timestamp = int(time.time())
    random_str = str(timestamp) + '_' + result_str
    return random_str

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

def add_background_music(video_file_path: str, audio_file_path: str, output_file_path: str, repeat_audio: bool=True, pause: float=1.0, volume: float=1.0) -> None:
    video = VideoFileClip(video_file_path)  # Existing Video File
    existing_audio = video.audio  # Existing Audio in Video File
    new_audio = AudioFileClip(audio_file_path)  # New Audio File
    new_audio = new_audio.fx(volumex, volume)  # Adjusting the volume of the new audio
    if repeat_audio:
        # Duration for the silent clip
        fps = 44100
        audio_array = np.zeros((int(pause*fps), 2))
        cl_silent = AudioArrayClip(audio_array, fps=fps)
        cl_silent.write_audiofile('silent.wav')
        audio_clips = [new_audio]
        silent_audio = AudioFileClip('silent.wav')
        # append audio clips until their total duration is greater than the video
        while sum(clip.duration for clip in audio_clips) < video.duration:
            audio_clips.extend([new_audio, silent_audio])
        new_audio = concatenate_audioclips(audio_clips)

    # If the new audio is longer than the video, limit its duration to that of the video.
    if new_audio.duration > video.duration:
        new_audio = new_audio.subclip(0, video.duration)
    elif video.duration > new_audio.duration:
        video = video.subclip(0, new_audio.duration)

    # If the video also has audio, we will overlay the new audio onto the existing audio
    if existing_audio is not None:
        audio = CompositeAudioClip([existing_audio, new_audio])
    else:
        audio = new_audio  # If the video has no audio, just set the new audio as the video's audio

    final_clip = video.set_audio(audio)  # Set the audio track of the video to the audio clip created above
    final_clip.write_videofile(output_file_path, audio_codec='aac')  # Write the output

def mindsflow_function(event, context) -> dict:
    video_url = event.get("video_url")
    audio_url = event.get("audio_url")
    volume = event.get("volume", 1.0)
    repeat_audio = event.get("repeat_audio", False)
    
    video_file_path = "temp_video.mp4"
    audio_file_path = "temp_audio.wav"
    random_str = get_random_string()
    output_file_path = f"output_{random_str}.mp4"
    
    # Step 1: download files
    download_file(video_url, video_file_path)
    download_file(audio_url, audio_file_path)
    
    # Step 2: add background music to video
    if volume > 0:
        add_background_music(video_file_path, audio_file_path, output_file_path, volume=volume, repeat_audio=repeat_audio)
    else:
        print('audio not added because specified volume was <= 0')
    
    # Step 3: upload file to S3
    url = upload_to_aws(output_file_path)
    
    result = {
        'video_url': url
    }
    return result

        