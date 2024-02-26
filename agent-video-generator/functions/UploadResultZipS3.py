"""$
{
    "name": "UploadResultZipS3",
    "displayName": "",
    "description": "UploadResultZipS3",
    "inputPattern": {
        "type": "object",
        "required": [
            "video_url",
            "title",
            "first_frame_url",
            "script",
            "description"
        ],
        "properties": {
            "title": {
                "type": "string",
                "description": ""
            },
            "script": {
                "type": "string",
                "description": ""
            },
            "video_url": {
                "type": "string",
                "description": ""
            },
            "description": {
                "type": "string",
                "description": ""
            },
            "first_frame_url": {
                "type": "string",
                "description": ""
            },
            "video_url_no_music": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "result_url"
        ],
        "properties": {
            "result_url": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "UploadVideo",
    "testCases": [
        {
            "script": "hello",
            "title": "title of the 对的 video 沙发",
            "first_frame_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/img_1697717278_uakysssz.png",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/output_1697717270_bmvbdbul.mp4",
            "description": "a video about something",
            "video_url_no_music": ""
        }
    ],
    "aiPrompt": "Upload result S3",
    "greeting": ""
}
$"""

import os
import urllib.request
import json
import shutil
import boto3
import unicodedata
import random
import string

# Auxiliary function to download video and image
def download_file(url, path):
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"An error occurred while downloading the file. Error: {str(e)}")
        return False

# Auxiliary function to write description and title in txt files
def write_txt_file(content, path):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"An error occurred while writing the text file. Error: {str(e)}")
        return False

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

    bucket_path = 'video-results'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'

    return url

# Auxiliary function to create a folder, download the files and then zip the folder
def prepare_files(event):
    video_url = event.get("video_url")
    image_url = event.get("first_frame_url")
    video_title = event.get("title")
    video_description = event.get("description")
    text = event.get("script")
    video_url_no_music = event.get("video_url_no_music", None)

    print(video_title)
    video_title_original = video_title
    if not video_title.isascii():
        video_title = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    if len(video_title) > 30:
        video_title = video_title[:30]
    video_title = video_title.replace(" ", "_")
    print(video_title)

    if not os.path.exists(video_title):
        os.makedirs(video_title)

    video_path = f"{video_title}/video.{video_url.split('.')[-1]}"
    download_file(video_url, video_path)
    img_path =  f"{video_title}/first_frame.{image_url.split('.')[-1]}"
    download_file(image_url, img_path)

    write_txt_file(video_description, f"{video_title}/description.txt")
    write_txt_file(video_title_original, f"{video_title}/{video_title}.txt")
    write_txt_file(text, f"{video_title}/text.txt")
    if video_url_no_music is not None:
        write_txt_file(video_url_no_music, f"{video_title}/video_url_no_music.txt")

    shutil.make_archive(video_title, 'zip', video_title)
    url = upload_to_aws(f"{video_title}.zip")

    os.remove(video_path)
    os.remove(img_path)
    os.remove(f"{video_title}.zip")
    shutil.rmtree(video_title)

    return url

# Main function
def mindsflow_function(event, context) -> dict:

    # prepare files and upload to S3
    s3_url = prepare_files(event)

    # define result
    result = {
        'result_url': s3_url
    }

    return result
        