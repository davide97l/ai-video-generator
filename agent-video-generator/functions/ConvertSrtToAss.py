"""$
{
    "name": "ConvertSrtToAss",
    "displayName": "",
    "description": "Converts srt file to ass file",
    "inputPattern": {
        "type": "object",
        "required": [
            "srt_url"
        ],
        "properties": {
            "shadow": {
                "type": "number",
                "description": ""
            },
            "marginl": {
                "type": "integer",
                "description": ""
            },
            "marginr": {
                "type": "integer",
                "description": ""
            },
            "marginv": {
                "type": "integer",
                "description": ""
            },
            "outline": {
                "type": "integer",
                "description": ""
            },
            "srt_url": {
                "type": "string",
                "description": ""
            },
            "fontname": {
                "type": "string",
                "description": "arial"
            },
            "fontsize": {
                "type": "integer",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "ass_url"
        ],
        "properties": {
            "ass_url": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "shadow": 0,
            "marginl": 0,
            "marginr": 0,
            "marginv": 0,
            "outline": 0,
            "srt_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/89z79p.srt",
            "fontname": "文泉驿正黑",
            "fontsize": 0
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import boto3
import os
import uuid
import requests
import pysubs2


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


def convert_srt_to_ass(srt_path: str, ass_path: str, fontname='Arial', fontsize=16, marginl=10, marginv=10, marginr=10, outline=0, shadow=0):
    subs = pysubs2.load(srt_path, encoding="utf-8")
    for line in subs:
        line.style = "my_style"
    subs.styles["my_style"] = pysubs2.SSAStyle(fontname=fontname, fontsize=fontsize,
                                               marginl=marginl, marginr=marginr,
                                               marginv=marginv, outline=outline,
                                               shadow=shadow)
    subs.save(ass_path)


def mindsflow_function(event, context) -> dict:
    srt_url = event.get("srt_url")
    fontname = event.get("fontname", "Arial")
    fontsize = event.get("fontsize", 10)
    marginl = event.get("marginl", 20)
    marginr = event.get("marginr", 20)
    marginv = event.get("marginv", 10)
    outline = event.get("outline", 1)
    shadow = event.get("shadow", 0)

    file_name = srt_url.split('/')[-1].split('.')[0]
    srt_file = f"{file_name}.srt"
    ass_file = f"{file_name}.ass"
    download_file(srt_url, srt_file)

    convert_srt_to_ass(srt_file, ass_file, fontname, fontsize, marginl, marginv, marginr, outline, shadow)

    upload_url = upload_to_aws(ass_file)

    os.remove(srt_file)
    os.remove(ass_file)

    result = {
        'ass_url': upload_url
    }

    return result

        