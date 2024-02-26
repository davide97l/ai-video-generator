"""$
{
    "name": "addAudioSegmentsToVideo",
    "displayName": "",
    "description": "Add audio segments to video",
    "inputPattern": {
        "type": "object",
        "required": [
            "voice",
            "json_url",
            "video_url",
            "audio_folder",
            "use_original_voice"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": ""
            },
            "json_url": {
                "type": "string",
                "description": ""
            },
            "video_url": {
                "type": "string",
                "description": ""
            },
            "audio_folder": {
                "type": "string",
                "description": ""
            },
            "use_original_voice": {
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
                "description": ""
            }
        }
    },
    "tag": "TextToSpeech",
    "testCases": [
        {
            "voice": "d8369f1b-588b-40b2-8009-3511630bff13_audio",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedAOjUGH.json",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/0ea5ed8d-795e-4120-993d-62bb9ba70920_video_no_audio.mp4",
            "audio_folder": "test",
            "use_original_voice": false
        },
        {
            "voice": "d8369f1b-588b-40b2-8009-3511630bff13_audio",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedAEAQmF.json",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/a53247d5-055c-464e-bdc3-242369f1ff46_video_no_audio.mp4",
            "audio_folder": "test",
            "use_original_voice": false
        },
        {
            "voice": "zh-CN-YunfengNeural",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedDLYYSi.json",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/combine_8d43656c-2e0c-48cd-a4b6-d8c1c0336740.mp4",
            "audio_folder": "test",
            "use_original_voice": false
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import moviepy.editor as mpy
import os
import requests
from pydub import AudioSegment
import shutil
import boto3


def download_file(url, filename):
    if not os.path.exists(filename):
        res = requests.get(url)
        with open(filename, "wb") as f:
            f.write(res.content)
    else:
        print(f"The file {filename} already exists.")


def get_captions_from_url(url):
    filename = f"{url.split('/')[-1]}"
    # download the json file
    download_file(url, filename)
    # read the contents
    with open(filename, 'r', encoding='utf-8') as f:
        captions = json.load(f)
    return captions, filename


def upload_to_aws(filename: str, bucket_path = None) -> str:
    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    s3_client = session.client('s3')
    if bucket_path is None:
        bucket_path = 'ai-video'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    return url


def delete_from_aws(filename: str, bucket_path=None):
    bucket_name = os.environ.get('bucket_name')
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    s3_client = session.client('s3')
    if bucket_path is None:
        bucket_path = 'ai-video'
    # Now delete the file after upload
    s3_client.delete_object(Bucket=bucket_name, Key=f"{bucket_path}/{filename}")


unit_time = 10000000


def combine_video_audio(video_path: str, captions, audio_folder: str, api_data: dict, voice_clone_url: str, use_original_voice: bool = False) -> str:
    # get the video
    video = mpy.VideoFileClip(video_path)
    audio_tracks = []

    # loop over all the start times
    for i, cap in enumerate(captions):
        # start time of audio
        start_time = cap['start_time'] / unit_time
        audio_path = f"{audio_folder}/audio_segment_{i+1}.wav"

        print(f'Processing audio {i+1} | Start time {start_time} | {audio_path}')

        if use_original_voice:
            audio_url = upload_to_aws(audio_path, bucket_path='temp-audio')
            headers = {'Content-Type': 'application/json'}
            api_data['audio_url'] = audio_url
            response = requests.post(voice_clone_url, data=json.dumps(api_data), headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f'Voice cloning failed with status code: {response.status_code}')
            audio_path = f'{audio_folder}/gen_voice_{i+1}.wav'
            print('use original voice', audio_path)
            with open(audio_path, 'wb') as file:
                file.write(response.content)
            delete_from_aws(audio_path, bucket_path='temp-audio')

        # load newly created voice track as an AudioFileClip
        new_audio = mpy.AudioFileClip(audio_path)
        # set start time for this audio segment
        new_audio = new_audio.set_start(start_time)
        # add this audio to the audio_tracks list
        audio_tracks.append(new_audio)

    print('Writing video...')
    # concatenate the original audio with new audio tracks
    final_audio = mpy.CompositeAudioClip(audio_tracks)
    # build final video with new audio track
    video = video.set_audio(final_audio)
    new_video_path = f"combine_{video_path}"
    if '_video_no_audio' in new_video_path:
        new_video_path = new_video_path.replace('_video_no_audio', '')
    video.write_videofile(new_video_path, audio_codec='aac')
    return new_video_path


def mindsflow_function(event, context) -> dict:
    video_url = event.get("video_url")
    json_url = event.get("json_url")
    audio_folder = event.get("audio_folder")
    voice = event.get('voice')
    use_original_voice = event.get('use_original_voice')
    api_ip = os.environ.get('api_ip')

    video_path = video_url.split('/')[-1]
    download_file(video_url, video_path)
    print(f'Video downloaded from {video_url}')
    captions, json_name = get_captions_from_url(json_url)

    voice_clone_url = f"http://{api_ip}:5001/generate_voice/"

    api_data = {
        "audio_url": None,
        "voice": voice,
        "clean_noise": False
    }

    # get the audio configuration result
    new_video_path = combine_video_audio(video_path, captions, audio_folder, api_data, voice_clone_url, use_original_voice)
    result_video = upload_to_aws(new_video_path)

    # delete local files after use
    os.remove(video_path)
    os.remove(new_video_path)
    os.remove(json_name)
    #shutil.rmtree(audio_folder)

    # define result
    result = {
        'video_url': result_video
    }

    return result
        