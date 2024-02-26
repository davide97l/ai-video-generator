"""$
{
    "name": "AddCaptionsToVideoMoviepy",
    "displayName": "",
    "description": "Add captions to video with moviepy",
    "inputPattern": {
        "type": "object",
        "properties": {
            "font_name": {
                "type": "string",
                "description": ""
            },
            "font_size": {
                "type": "number",
                "description": ""
            },
            "video_url": {
                "type": "string",
                "description": ""
            },
            "text_color": {
                "type": "string",
                "description": ""
            },
            "caption_url": {
                "type": "string",
                "description": ""
            },
            "text_bg_color": {
                "type": "string",
                "description": ""
            },
            "highlight_color": {
                "type": "string",
                "description": ""
            },
            "text_bg_opacity": {
                "type": "number",
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
        },
        "required": [
            "video_url",
            "caption_url"
        ]
    },
    "outputPattern": {
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",
                "description": ""
            }
        },
        "required": [
            "video_url"
        ]
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "font_name": "Heebo",
            "font_size": 30,
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/teacher_comic.mp4",
            "text_color": "white",
            "caption_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/test.srt",
            "text_bg_color": "black",
            "highlight_color": "yellow",
            "text_bg_opacity": 0.5,
            "caption_position": "bottom",
            "text_border_size": 0,
            "text_border_color": ""
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import pysrt
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips
import os
import requests
import boto3
import random, string
import ast

font_dir = os.environ['font_dir']

color_dict = {
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'yellow': (255, 255, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    'grey': (128, 128, 128),
    'pink': (255, 192, 203),
    'purple': (128, 0, 128),
    'orange': (255, 165, 0),
    'brown': (165, 42, 42)
}

def download_file(url, filename):
    response = requests.get(url)
    file = open(filename, 'wb')
    file.write(response.content)
    file.close()

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

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


def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000


llm_prompt = 'Given the input text, choose some important and meaningful words to highlight. Max 1-2 words per sentence. Return them as a python list.\nTEXT: {}'
def highlight_words(input_str: str, event) -> str:
    input_str = llm_prompt.format(input_str)
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1548
    }
    resp = event.chat.messages(data=data)
    return resp


def create_subtitle_clips(subtitles, videosize, fontsize=24, font='fonts/Caveat.ttf', color='yellow', bg_color='black', border_size=1.5, border_color="black", caption_position='bottom', bg_opacity=0.5, highlight_color=None, event=None):
    subtitle_clips = []

    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time

        video_width, video_height = videosize

        if border_size == 0 or border_size == 0.:
            border_color = None
        
        method = 'caption'
        if highlight_color is not None:
            # https://docs.gtk.org/Pango/pango_markup.html
            important_words = ast.literal_eval(highlight_words(subtitle.text, event))
            print('Important words:', important_words)
            for word in important_words:
                subtitle.text = subtitle.text.replace(word,  f'<span foreground="{rgb_to_hex(color_dict[highlight_color])}">{word}</span>')
            method = 'pango'
            subtitle.text = f'<b>{subtitle.text}</b>'

        text_clip = TextClip(subtitle.text, fontsize=fontsize, font=font, color=color, size=(video_width*3/4, None), method=method, stroke_color=border_color, stroke_width=border_size).set_start(start_time).set_duration(duration)

        # add bg color
        if bg_color in color_dict.keys():
            im_width, im_height = text_clip.size
            color_clip = ColorClip(size=(int(im_width), int(im_height)), color=color_dict[bg_color])
            color_clip = color_clip.set_opacity(bg_opacity).set_start(start_time).set_duration(duration)
            text_clip = CompositeVideoClip([color_clip, text_clip])

        subtitle_x_position = 'center'
        y_position_dict = {
            'center': 'center',
            'bottom': video_height * 4/5,
            'top': video_height * 1/5,
        }
        subtitle_y_position = y_position_dict[caption_position]

        text_position = (subtitle_x_position, subtitle_y_position)
        subtitle_clips.append(text_clip.set_position(text_position))

    return subtitle_clips


def mindsflow_function(event, context) -> dict:

    caption_url = event.get("caption_url")
    video_url = event.get("video_url")
    fontsize = event.get("font_size", 24)
    fontname = event.get("font_name", "SourceSerif4")
    text_color = event.get('text_color', 'white')
    bg_color = event.get('text_bg_color', 'black')
    bg_opacity = event.get('text_bg_opacity', 0.5)
    border_size = event.get('text_border_size', 1.)
    border_color = event.get('text_border_color', None)
    caption_position = event.get('caption_position', 'center')
    highlight_color = event.get('highlight_color', None)
    fontname = f'{font_dir}/{fontname}.ttf'

    mp4_path = video_url.split('/')[-1]
    caption_path = caption_url.split('/')[-1]
    download_file(video_url, mp4_path)
    download_file(caption_url, caption_path)

    if highlight_color not in color_dict.keys():
        highlight_color = None

    # Load video and SRT file
    video = VideoFileClip(mp4_path)
    subtitles = pysrt.open(caption_path)

    # Set output path
    output_path = "video_with_captions_{}.mp4".format(''.join(random.choices(string.ascii_letters + string.digits, k=5)))

    # Create subtitle clips
    subtitle_clips = create_subtitle_clips(subtitles, video.size, fontsize, fontname, text_color, bg_color, border_size, border_color, caption_position, bg_opacity, highlight_color, event)

    # Add subtitles to the video
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # Write output video file
    final_video.write_videofile(output_path)

    upload_url = upload_to_aws(output_path)
    os.remove(output_path)
    os.remove(caption_path)
    os.remove(mp4_path)

    result = {
        'video_url': upload_url
    }

    return result

        