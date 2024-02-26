"""$
{
    "name": "AddCaptionsToVideoOpenCV",
    "displayName": "",
    "description": "The Python method is intended to download a video from a given URL, add captions to that downloaded video, upload the updated video to an S3 bucket, and return a URL for accessing the newly uploaded video.",
    "inputPattern": {
        "type": "object",
        "required": [
            "video_url",
            "json_caption"
        ],
        "properties": {
            "margin": {
                "type": "number",
                "description": ""
            },
            "font_size": {
                "type": "number",
                "description": ""
            },
            "font_type": {
                "type": "string",
                "description": ""
            },
            "video_url": {
                "type": "string",
                "description": "URL of the video to be downloaded"
            },
            "text_color": {
                "type": "string",
                "description": ""
            },
            "border_color": {
                "type": "string",
                "description": ""
            },
            "json_caption": {
                "type": "string",
                "description": "Captions to be added to the video"
            },
            "max_caption_len": {
                "type": "number",
                "description": ""
            },
            "caption_position": {
                "type": "string",
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
                "description": "The URL of the video uploaded to S3"
            }
        }
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "margin": 0.1,
            "font_size": 30,
            "font_type": "default",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/a78d8376-a5f9-413c-9624-b4eb7680357e_video_no_audio.mp4",
            "text_color": "white",
            "border_color": "black",
            "json_caption": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedBDbUzJ.json",
            "max_caption_len": 40,
            "caption_position": "threequarter"
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
    result_str = ''.join(random.choice(letters) for _ in range(8))
    timestamp = int(time.time())
    random_str = str(timestamp) + '_' + result_str
    return random_str

# Define color dictionary for known colors
color_dict = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'red': (0, 0, 255),  # Remember, in OpenCV it's BGR not RGB
    'green': (0, 255, 0),
    'blue': (255, 0, 0),
    'yellow': (0, 255, 255)
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

def add_captions(video_path, json_file_path, border_size=2, border_color='black', text_color='white',
                 font_size=30, font_type='DUPLEX', caption_position='bottom', outfile="out.mp4", margin=0.1,
                 font_dir=''):
    # Load video
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Load the JSON file with caption details
    with open(json_file_path, 'r') as f:
        captions = json.load(f)
    print(captions)

    # Get the specified color tuples
    border_color = color_dict[border_color.lower()]
    text_color = color_dict[text_color.lower()]
    # Get the specified font
    if font_type is None:
        font_type = 'default'
    if font_type in font_dict.keys():
        font_type = font_dict[font_type]
    font = ImageFont.truetype(f'{os.path.join(font_dir, font_type)}.ttf', size=font_size)

    # Define the codec and create a VideoWriter object
    #fourcc_code = int(cap.get(cv2.CAP_PROP_FOURCC))
    #fourcc_code = "".join([chr((fourcc_code >> 8 * i) & 0xFF) for i in range(4)])
    fourcc_code = "vp90"
    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
    out = cv2.VideoWriter(outfile, fourcc, fps, (width, height))

    frame_counter = 0
    caption_index = 0
    print('fps', fps)
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret:
            current_time = frame_counter * (1e7/fps)  # Current timestamp in microseconds
            print(current_time / 1e7, captions[caption_index], caption_index)
            print(frame_counter, caption_index)
            if current_time >= captions[caption_index]['end_time']:
                caption_index += 1
                # Check if there are no more captions
                if caption_index >= len(captions):
                    break  # If no more captions, exit loop

            img_pil = Image.fromarray(frame)
            draw = ImageDraw.Draw(img_pil)

            margin_rate = int(width * margin)

            lines = wrap_text(captions[caption_index]['sentence'], width - 2 * margin_rate, font)
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

                for k in range(-border_size, border_size+1):
                    for j in range(-border_size, border_size+1):
                        draw.text((textX+j, textY+k), line, font = font, fill = border_color)
                draw.text((textX, textY), line, font = font, fill = text_color)

            out.write(np.array(img_pil))

            frame_counter += 1

        else:
            break

    cap.release()
    out.release()

def mindsflow_function(event, context) -> dict:
        # get the video url and caption from the event
    video_url = event.get("video_url")
    captions_url = event.get("json_caption")
    caption_position = event.get("caption_position", "bottom")
    border_color = event.get("border_color", "black")
    text_color = event.get("text_color", "white")
    font_size = event.get("font_size", 30)
    max_caption_len = event.get("max_caption_len", 30)
    margin = event.get("margin", 0.1)
    font_type = event.get("font_type", 'default')

    download_path = "video_" + get_random_string() + ".mp4"
    out_path = "video_" + get_random_string() + ".mp4"
    download_file(video_url, download_path)

    json_path = "caption_" + get_random_string() + ".json"
    download_file(captions_url, json_path)

    # get the captioned video URL
    add_captions(download_path,
        json_file_path=json_path,
        outfile=out_path,
        caption_position=caption_position,
        border_color=border_color,
        text_color=text_color,
        font_size=font_size,
        margin=margin,
        font_type=font_type,
        font_dir = os.environ.get('font_dir')
    )

    # upload the combined image to aws and save the url
    url = upload_to_aws(out_path)

    # define result
    result = {
        'video_url': url
    }

    if os.path.exists(download_path):
        os.remove(download_path)
    if os.path.exists(json_path):
        os.remove(json_path)

    return result


        