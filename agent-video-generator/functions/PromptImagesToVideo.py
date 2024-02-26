"""$
{
    "name": "PromptImagesToVideo",
    "displayName": "",
    "description": "Utilizes an AI model to generate a specified number of images based on a given prompt and seed, which are then assembled into a video. Each image is displayed for a certain duration of time.",
    "inputPattern": {
        "type": "object",
        "properties": {
            "fps": {
                "type": "integer",
                "description": ""
            },
            "zoom": {
                "type": "number",
                "description": ""
            },
            "topic": {
                "type": "string",
                "description": "if present, help defining prompt"
            },
            "width": {
                "type": "integer",
                "description": "width"
            },
            "height": {
                "type": "integer",
                "description": "height"
            },
            "img_model": {
                "type": "string",
                "description": ""
            },
            "img_prompt": {
                "type": "string",
                "description": "Prompt to be converted into an image"
            },
            "crop_method": {
                "type": "string",
                "description": ""
            },
            "image_duration": {
                "type": "number",
                "description": ""
            },
            "video_duration": {
                "type": "number",
                "description": ""
            },
            "negative_prompt": {
                "type": "string",
                "description": ""
            },
            "transition_time": {
                "type": "number",
                "description": ""
            },
            "img_style_prompt": {
                "type": "string",
                "description": "Add adjectives to describe image"
            },
            "sentences_json_url": {
                "type": "string",
                "description": ""
            },
            "transition_overlap": {
                "type": "boolean",
                "description": ""
            }
        },
        "required": [
            "width",
            "height"
        ]
    },
    "outputPattern": {
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",
                "description": "The path to the generated video"
            },
            "first_frame_url": {
                "type": "string",
                "description": ""
            }
        },
        "required": [
            "video_url"
        ]
    },
    "tag": "VideoGeneration",
    "testCases": [
        {
            "fps": 4,
            "zoom": 1,
            "topic": "benefits of eating mango",
            "width": 1024,
            "height": 1792,
            "img_model": "dalle3",
            "img_prompt": "benefits of eating mango",
            "crop_method": "",
            "image_duration": 0,
            "video_duration": 0,
            "negative_prompt": "disfigured, bad anatomy, blurry, low resolution, ugly, mutilated, multiple pictures, collage",
            "transition_time": 1,
            "img_style_prompt": "",
            "sentences_json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/sentence_times_1703164123_tcocwjzo.json",
            "transition_overlap": true
        },
        {
            "fps": 0,
            "zoom": 0,
            "topic": "",
            "width": 0,
            "height": 0,
            "img_model": "",
            "img_prompt": "",
            "crop_method": "",
            "image_duration": 0,
            "video_duration": 0,
            "negative_prompt": "",
            "transition_time": 0,
            "img_style_prompt": "",
            "sentences_json_url": "",
            "transition_overlap": false
        },
        {
            "fps": 0,
            "zoom": 0,
            "topic": "",
            "width": 0,
            "height": 0,
            "img_model": "",
            "img_prompt": "",
            "crop_method": "",
            "image_duration": 0,
            "video_duration": 0,
            "negative_prompt": "",
            "transition_time": 0,
            "img_style_prompt": "",
            "sentences_json_url": "",
            "transition_overlap": false
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import numpy as np
from PIL import Image
import os
from tqdm import tqdm
import cv2
import boto3
import time
import random
import string
import requests
import math
from moviepy.editor import *
import subprocess
import uuid
from openai import OpenAI

'''command = 'pip install replicate'
process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)'''
import replicate

azure_time_unit = 10000000

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

def download_json(url: str):
    response = requests.get(url)
    data = response.json()
    return data

def resize_image(image_path, new_width, new_height):
    img = Image.open(image_path) # Open an image file
    img = img.resize((new_width, new_height), Image.LANCZOS) # Resize the image
    img.save(image_path) # Save the image back to original file

def crop_image(image_path, new_width, new_height):
    # Open the image file
    img = Image.open(image_path)
    width, height = img.size   # Get dimensions
    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2
    img = img.crop((left, top, right, bottom))
    img.save(image_path)

models = {
    'sd': "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
    'sdxl': "stability-ai/sdxl:1bfb924045802467cf8869d96b231a12e6aa994abfe37e337c63a4e49a8c6c41",
    'playground': "playgroundai/playground-v2-1024px-aesthetic:42fe626e41cc811eaf02c94b892774839268ce1994ea778eba97103fe1ef51b8",
    'kandinsky': "ai-forever/kandinsky-2.2:ea1addaab376f4dc227f5368bbd8eff901820fd1cc14ed8cad63b29249e9d463",
    'dalle3': "dall-e-3"
}

def generate_image(prompt: str, width: int=1024, height: int=1024, model: str='sd', negative_prompt: str='') -> str:
    retries = 5
    for retry in range(retries):
        try:
            if model in ['sd', 'sdxl', 'playground', 'kandinsky']:
                output = replicate.run(
                    models[model],
                    input={
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "negative_prompt": negative_prompt,
                        "num_outputs": 1}
                )
            elif model in ['dalle3']:
                client = OpenAI()
                size = f"{width}x{height}"
                print(size, prompt, model)
                response = client.images.generate(
                    model=models[model],
                    prompt=prompt,
                    n=1,
                    quality='hd',
                    size=size,  # 1792x1024, 1024x1792
                    style='vivid',  # vivid or natural
                )
                output = [response.data[0].url]
            return output[0]
        except Exception as e:
            if retry < retries - 1: # Don't sleep for last attempt
                time.sleep(1)  # Wait a bit before trying again
            else:
                raise e
    return output[0]

llm_prompt = 'Given the input sentence, generate a suitable prompt for an image generation model that can generate an image corresponding to the input. Make the prompt as descriptive as possible but keep it short.\nINPUT: {}.\nOUTPUT:'
def generate_img_prompt(input_str: str, event) -> str:
    input_str = llm_prompt.format(input_str)
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1548
    }
    resp = event.chat.messages(data=data)
    return resp

def concatenate_images(event):

    img_prompt = event.get("img_prompt", None) # prompt used to generate images, Ignored if provided video transcription (sentences_json_url)
    img_style_prompt = event.get("img_style_prompt", "")
    negative_prompt = event.get("negative_prompt", "")
    width = event.get("width")
    height = event.get("height")
    transcript_json_url = event.get("sentences_json_url", None) # video transcription
    image_duration = event.get("image_duration", 3)
    video_duration = event.get("video_duration", 10) # durations in s of the video to generate. Ignored if provided video transcription (sentences_json_url)
    model = event.get("img_model", 'sd') # model used to generate images. ['sd', 'sdxl']
    crop_method = event.get("crop_method", None) # method used to crop generated image to fit desired size. None=no crop. Accepted values in  [ 'resize',  'crop_center']
    fps = event.get("fps", 30)  # frame per second
    transition_time = event.get("transition_time", 1.) # duration of transition
    transition_overlap = event.get("transition_overlap", False) # whether transitions have overlpa
    zoom = event.get("zoom", 1.)  # zoom into image to create motion effect, > 1 to apply zoom
    topic = event.get("topic", None)  # if present, helps defining prompt

    # download the video transcript from the url, make prompt and compute fpm from transcription
    if transcript_json_url is not None:
        subtitles_json = download_json(transcript_json_url)
        durations = []
        frames_per_image = []
        img_prompts = []

        for i, item in enumerate(subtitles_json):
            if i < len(subtitles_json) - 1:
                duration = (subtitles_json[i+1]['start_time']  - item['start_time']) / float(azure_time_unit)
            else:
                duration = item['duration'] / float(azure_time_unit)
            durations.append(duration)
            if i !=0:
                duration += transition_time * transition_overlap
            if topic is not None and len(topic) > 1:
                sentence = f'{topic}, {item["sentence"]}'
            else:
                sentence = item['sentence']
            img_prompt = generate_img_prompt(sentence, event)
            if isinstance(img_style_prompt, str) and len(img_style_prompt) > 1:
                img_prompt = f'{img_prompt}, {img_style_prompt}'
            img_prompts.append(img_prompt)
            #print(item['sentence'], duration, img_prompt)
            frames_per_image.append(duration * fps)
        number_of_images = len(frames_per_image)
    else:  # make prompt and compute fpm from video duration and image duration
        if isinstance(video_duration, float):
            video_duration = math.ceil(video_duration)
        number_of_images = max(int(video_duration / image_duration), 1)
        if isinstance(img_style_prompt, str) and len(img_style_prompt) > 1:
            img_prompt = f'{img_prompt}, {img_style_prompt}'
        img_prompts = [img_prompt] * number_of_images
        fpm = int(video_duration * fps / number_of_images)
        frames_per_image = [fpm] + [(fpm + int(fps * transition_time) * transition_overlap)] * (number_of_images - 1)
    
    print('image prompts:', img_prompts)
    print('number of images:', number_of_images)
    print('number of frames:', sum(frames_per_image))

    video_path = f'video_{uuid.uuid4().hex[:6]}.mp4'

    frames_url = []
    video_clips = []
    for i in range(number_of_images):
        
        # Generate and download the image
        if crop_method not in [ 'resize',  'crop_center']:
            img_url = generate_image(img_prompts[i], width, height, model, negative_prompt)
        else:
            img_url = generate_image(img_prompts[i], 1024, 1024, model, negative_prompt)
        img_path = f'ai-img_{uuid.uuid4().hex[:6]}.png'
        download_file(img_url, img_path)

        # crop if required
        if crop_method == 'resize':
            resize_image(img_path, width, height)
        elif crop_method == 'crop_center':
            crop_image(img_path, width, height)
        
        # upload first frame to S3
        if i == 0:
            frame_url = upload_to_aws(img_path)
            frames_url.append(frame_url)

        # make clip from frame
        screensize = (width, height)
        img_duration = frames_per_image[i] / fps
        # add zoom if required
        if zoom != 1. and zoom != 1:
            clip = (ImageClip(img_path)
                    .resize(height=screensize[1]*4)
                    .resize(lambda t: 1 + (zoom-1.)*t / img_duration)
                    .set_position(('center', 'center'))
                    .set_duration(frames_per_image[i] / fps)
                    )
            clip = CompositeVideoClip([clip]).resize(width=screensize[0])
            vid = CompositeVideoClip([clip.set_position(('center', 'center'))], size=screensize)
        else:
            vid = (ImageClip(img_path) .set_duration(frames_per_image[i] / fps))
        video_clips.append(vid)
        
        # delete current frame to save memory
        if os.path.exists(img_path):
            os.remove(img_path)

    video_clip = concatenate_videoclips(video_clips)

    # load the video which was just created and add transitions
    if transition_time == 0 or transition_time == 0.:
        video_clip.write_videofile(video_path, fps=fps)
        return video_path, frames_url[0]

    clip = video_clip
    clips = []

    # split the video into clips, each equivalent to the duration of a frame and add transition effects
    start_time, end_time = 0., 0.
    for i in range(number_of_images):
        end_time = start_time + frames_per_image[i] / fps # end time of the clip in the original video
        #print(start_time, end_time)
        if i == 0:
            clips.append(clip.subclip(start_time, end_time))
        else:
            clips.append((clip.subclip(start_time, end_time).set_start(start_time - transition_time * i * transition_overlap)).crossfadein(transition_time))
        start_time = end_time
    # Combine all the clips back into a single video.
    final_clip = CompositeVideoClip(clips)
    #print('Duration:', final_clip.duration)

    # Overwrite the original video with the final clip with transitions.
    video_path = 'trs_' + video_path
    final_clip.write_videofile(video_path, fps=fps)

    return video_path, frames_url[0]

def mindsflow_function(event, context) -> dict:
    # Generate images from the prompt and concatenate them to form a video.
    video_path, first_frame_url = concatenate_images(event)

    url = upload_to_aws(video_path)

    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists('trs_' + video_path):
        os.remove('trs_' + video_path)

    # Define result
    result = {
        'video_url': url,
        'first_frame_url': first_frame_url
    }

    return result

        