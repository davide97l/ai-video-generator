"""$
{
    "name": "extractVideoAudioComponents",
    "displayName": "",
    "description": "This method is designed to download a YouTube video, extract its audio, and upload the video without audio and the extracted audio to an S3 server, returning the respective URLs. It is presented in a way that allows for future adaptation to other platforms.",
    "inputPattern": {
        "type": "object",
        "required": [
            "video_url"
        ],
        "properties": {
            "video_url": {
                "type": "string",
                "description": "The URL of the video to be downloaded and split"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "audio_url",
            "video_url"
        ],
        "properties": {
            "audio_url": {
                "type": "string",
                "description": "The url for the downloaded audio file"
            },
            "video_url": {
                "type": "string",
                "description": "The url for the downloaded video file without audio"
            },
            "original_video_url": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "DataPreprocessing",
    "testCases": [
        {
            "video_url": "https://www.youtube.com/watch?app=desktop&v=Lv06Razi3Y4"
        },
        {
            "video_url": "https://www.bilibili.com/video/BV14d4y1U7iG/"
        },
        {
            "video_url": "https://www.instagram.com/reel/Cx43zhAvdwL/"
        },
        {
            "video_url": "https://www.tiktok.com/@tedtoks/video/7304757623600057631"
        }
    ],
    "aiPrompt": "Given the URL of a video youtube, download it, extract the audio. Upload the video without audio and the audio to S3 and return the corresponding URLs. Make the code such the download can be generalized to other platforms in the future",
    "greeting": ""
}
$"""

import json
from pytube import YouTube
from moviepy.editor import *
import boto3
import uuid
import os
from pydub import AudioSegment
import youtube_dl
import requests
import instaloader
from urllib.parse import urlparse

def extract_reel_id(url):
    path = urlparse(url).path
    segments = path.split('/')
    if "reel" in segments:
        reel_index = segments.index("reel")
        if reel_index+1 < len(segments):
            return segments[reel_index+1]
    return None

s3_client = boto3.client('s3')

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

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
}

def download_and_split_video(url, download_path=""):
    if 'youtube.com' in url:
        yt = YouTube(url)
        try:
            print('try download 720p')
            video = yt.streams.get_by_resolution('720p').download(download_path)
        except:
            print('download failed')
            video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(download_path)
    elif 'www.bilibili.com' in url:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = ydl.prepare_filename(info_dict)
            video = os.path.join(download_path, video_title.replace('flv', 'mp4'))
    elif 'www.tiktok.com' in url:
        # pip install yt-dlp
        video_name = url.split('/')[-1]
        video = f"tiktok_video_{video_name}.mp4"
        os.system("yt-dlp {} -o {}".format(url, video))
    elif 'www.instagram.com' in url:  # currently not working
        reel_id = extract_reel_id(url)
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, reel_id)
        video_url = post.video_url
        video_name = f'ins_reel_{reel_id}'
        video = video_name + '.mp4'
        from datetime import datetime, timedelta
        L.download_pic(filename=video_name, url=url, mtime=datetime.now())
    else: 
        response = requests.get(url)
        video = os.path.join(download_path, url.split('/')[-1])
        with open(video, 'wb') as file:
            file.write(response.content)

    video_clip = VideoFileClip(video)
    audio = video_clip.audio
    video_without_audio = video_clip.without_audio()
    audio_file = os.path.join(download_path, f'{str(uuid.uuid4())}_audio')
    
    # Save audio to wav 
    audio.write_audiofile(audio_file + ".wav")
    
    # Save the video file without audio
    video_file = os.path.join(download_path, f'{str(uuid.uuid4())}_video_no_audio.mp4')
    video_without_audio.write_videofile(video_file, audio=False)
    
    return audio_file + ".wav", video_file, video

def mindsflow_function(event, context) -> dict:
    url = event.get("video_url")
    audio_file, video_file, original_video = download_and_split_video(url)
    audio_url = upload_to_aws(audio_file)
    video_url = upload_to_aws(video_file)
    original_video_url = upload_to_aws(original_video)
    os.remove(original_video)
    os.remove(audio_file)
    os.remove(video_file)
    result = {
        'audio_url': audio_url,
        'video_url': video_url,
        'original_video_url': original_video_url
    }
    return result

        