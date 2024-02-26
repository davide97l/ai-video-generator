"""$
{
    "name": "AddCaptionsToVideoFFMPEG",
    "displayName": "",
    "description": "This method receives an SRT or ASS subtitle file path and an MP4 video file path as inputs. Using the FFmpeg library, it integrates the subtitle file with the video and outputs the path of the combined video. It does not operate in command-line mode",
    "inputPattern": {
        "type": "object",
        "required": [
            "video_url",
            "captions_url"
        ],
        "properties": {
            "video_url": {
                "type": "string",
                "description": "Path to the MP4 video file."
            },
            "captions_url": {
                "type": "string",
                "description": "Path to the ASS (Advanced SubStation Alpha) subtitle file."
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
                "description": "Path of the video file after merging with subtitles"
            }
        }
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/output_1701831655_ypexkwiz.mp4",
            "captions_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/WQ7TEooutput_file.ass"
        }
    ],
    "aiPrompt": "AddCaptionsToVideoFFMPEG",
    "greeting": ""
}
$"""

import os
import ffmpeg
import requests
import boto3
import random, string
import subprocess

def download_file(url, filename):
    response = requests.get(url)
    file = open(filename, 'wb')
    file.write(response.content)
    file.close()

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

def merge_subtitle_and_video(subtitle_path: str, mp4_path: str, output_path: str):
    # determine file type from extension
    _, file_extension = os.path.splitext(subtitle_path)

    if file_extension.lower() == ".srt":
        ffmpeg.input(mp4_path).output(output_path, vf='subtitles=' + subtitle_path).run(overwrite_output=True)
    elif file_extension.lower() == ".ass":
        command = f"ffmpeg -i {mp4_path} -vf 'ass={subtitle_path}' {output_path}"
        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
        output = process.stdout
    else:
        print(f"Unsupported subtitle file type: {file_extension}")

def mindsflow_function(event, context) -> dict:
    # get the srt path from the event
    caption_url = event.get("captions_url")
    # get the mp4 path from the event
    video_url = event.get("video_url")

    command = ' apt install ffmpeg'
    process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)

    mp4_path = video_url.split('/')[-1]
    caption_path = caption_url.split('/')[-1]
    download_file(video_url, mp4_path)
    download_file(caption_url, caption_path)

    # Set output path
    output_path = "video_with_captions_{}.mp4".format(''.join(random.choices(string.ascii_letters + string.digits, k=5)))

    # Merge the srt and mp4 files
    merge_subtitle_and_video(ass_path, mp4_path, output_path)

    upload_url = upload_to_aws(output_path)
    os.remove(output_path)

    # define result
    result = {
        'video_url': upload_url
    }

    return result

        