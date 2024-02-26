"""$
{
    "name": "addTextToImage",
    "displayName": "",
    "description": "This Python method downloads an image from a provided URL, adds a given title to the image, uploads the modified image to an S3 bucket, and then returns the new image's URL.",
    "inputPattern": {
        "type": "object",
        "required": [
            "text",
            "image_url"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": ""
            },
            "margin": {
                "type": "number",
                "description": ""
            },
            "font_name": {
                "type": "string",
                "description": ""
            },
            "font_size": {
                "type": "number",
                "description": ""
            },
            "image_url": {
                "type": "string",
                "description": "URL of the video to be downloaded"
            },
            "text_color": {
                "type": "string",
                "description": ""
            },
            "caption_position": {
                "type": "string",
                "description": ""
            },
            "text_border_size": {
                "type": "number",
                "description": ""
            },
            "text_border_color": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "image_url"
        ],
        "properties": {
            "image_url": {
                "type": "string",
                "description": "The presigned URL for the image uploaded to the S3 bucket"
            }
        }
    },
    "tag": "VideoGeneration",
    "testCases": [
        {
            "text": "",
            "margin": 0,
            "font_name": "",
            "font_size": 0,
            "image_url": "",
            "text_color": "",
            "caption_position": "",
            "text_border_size": 0,
            "text_border_color": ""
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import cv2
from moviepy.editor import VideoFileClip
import boto3
import os
import time
import random
import string
import requests
import numpy as np
from PIL import ImageFont, ImageDraw, Image

font_url = 'https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/fonts/{}.ttf'

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

def download_file(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)

def get_random_string():
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for _ in range(6))
    timestamp = int(time.time())
    random_str = str(timestamp) + '_' + result_str
    return random_str

# Define color dictionary for known colors
color_dict = {
'black': (0, 0, 0),
'white': (255, 255, 255),
'red': (0, 0, 255), # Remember, in OpenCV it's BGR not RGB
'green': (0, 255, 0),
'blue': (255, 0, 0),
'yellow': (0, 255, 255),
'cyan': (255, 255, 0),
'magenta': (255, 0, 255),
'light gray': (211, 211, 211),
'dark gray': (169, 169, 169),
'pink': (147, 20, 255),
'purple': (128, 0, 128),
'orange': (0, 165, 255),
'brown': (42, 42, 165)
}

# Define the dictionary for known font types
font_dict = {
    'chinese': 'NotoSansSC',
    'default': 'SourceSerif4',
}

def wrap_text(caption, frame_width, font):
    words = caption.split(' ')
    lines = [words.pop(0)]  # Initial
    for word in words:
        box = font.getbbox(lines[-1] + ' ' + word)
        text_width, text_height = box[2] - box[0], box[3] - box[1]
        if text_width > frame_width:
            lines.append(word)
        else:
            lines[-1] += ' ' + word
    return lines

def add_title_to_img(image_path, caption, outfile='out.jpg', border_size=2, border_color='black', text_color='white',
                       font_size=30, font_type='DUPLEX', caption_position='bottom', margin=0.1, font_dir=''):
    # Load image
    img_pil = Image.open(image_path)
    draw = ImageDraw.Draw(img_pil)

    width, height = img_pil.size

    # Get the specified font
    if font_type is None:
        font_type = 'default'
    if font_type in font_dict.keys():
        font_type = font_dict[font_type]
    try:
        font = ImageFont.truetype(f'{os.path.join(font_dir, font_type)}.ttf', size=font_size)
    except:
        if not os.path.exists(font_dir):
            os.makedirs(font_dir)
        download_file(font_url.format(font_type), f'{os.path.join(font_dir, font_type)}.ttf')
        font = ImageFont.truetype(f'{os.path.join(font_dir, font_type)}.ttf', size=font_size)

    margin_rate = int(width * margin)

    lines = wrap_text(caption, width - 2 * margin_rate, font)
    for i, line in enumerate(lines):
        box = font.getbbox(line)
        text_width, text_height = box[2] - box[0], box[3] - box[1]
        text_height = font_size * 1.3

        # Center the text
        textX = (width - text_width - margin_rate * 2) // 2 + margin_rate
        total_lines = len(lines)
        total_text_height = total_lines * text_height # The total height of text block

        # Position text as per given caption_position
        if caption_position.lower() == 'top':
            textY = margin_rate + (i * text_height)
        elif caption_position.lower() == 'bottom':
            textY = height - margin_rate - (len(lines) - i) * text_height
        elif caption_position.lower() == 'threequarter':
            three_quarter_height = height * 0.75
            textY = three_quarter_height - ((total_lines - i) * text_height)
        elif caption_position.lower() == 'onequarter':
            one_quarter_height = height * 0.25
            textY = one_quarter_height + ((i + 1) * text_height)
        else:  # Default to center if unknown value
            textY = ((height - total_text_height) // 2) + (i * text_height)

        # Draw the outline
        for k in range(-border_size, border_size + 1):
            for j in range(-border_size, border_size + 1):
                draw.text((textX + j, textY + k), line, font=font, fill=border_color)
        # Draw the text
        draw.text((textX, textY), line, font=font, fill=text_color)

    # save the image with caption
    img_pil.save(outfile)

def mindsflow_function(event, context) -> dict:
    img_url = event.get("image_url")
    text = event.get("text")
    caption_position = event.get("caption_position", "bottom")
    border_color = event.get("text_border_color", "black")
    text_color = event.get("text_color", "white")
    font_size = event.get("font_size", 30)
    margin = event.get("margin", 0.1)
    font_type = event.get("font_name", 'default')
    border_size = event.get("text_border_size", 2)
    
    download_path = "img_" + get_random_string() + ".png"
    out_path = "img_" + get_random_string() + ".png"
    download_file(img_url, download_path)
    # add title to the image
    add_title_to_img(download_path, 
        text,
        outfile=out_path,
        caption_position=caption_position,
        border_color=border_color,
        text_color=text_color,
        font_size=font_size,
        margin=margin,
        font_type=font_type,
        border_size=border_size,
        font_dir = os.environ.get('font_dir')
    )
    # upload the image to s3 and get the url
    url = upload_to_aws(out_path)
    
    # define result
    result = {
        'image_url': url
    }

    os.remove(download_path)
    os.remove(out_path)

    return result

        