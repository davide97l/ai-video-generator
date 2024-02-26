"""$
{
    "name": "generateSrtFromJson",
    "displayName": "",
    "description": "This Python method downloads a JSON file from a given URL which contains captions with their respective start, end, and duration time. It processes this data, generates a subtitle (SRT) file, and subsequently uploads it to S3 storage.",
    "inputPattern": {
        "type": "object",
        "required": [
            "sentences_json_url"
        ],
        "properties": {
            "min_words_sentence": {
                "type": "integer",
                "description": ""
            },
            "sentences_json_url": {
                "type": "string",
                "description": "URL of the JSON file containing the subtitles to be downloaded"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "srt_url"
        ],
        "properties": {
            "srt_url": {
                "type": "string",
                "description": "The status of the function operation"
            }
        }
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "min_words_sentence": 5,
            "sentences_json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/sentence_times_1703164123_oewslyvu.json"
        },
        {
            "min_words_sentence": 0,
            "sentences_json_url": ""
        }
    ],
    "aiPrompt": "Given the url of a json, download it. It contains some captions with their start, end and duration. The json is a list in this format\nsentence: \"今日话题做题速度太慢 怎么办？\"\nstart_time: 6000000\nend_time: 35500000\nduration: 29500000\nfrom it generate a srt file containing subtitles and upload it so s3",
    "greeting": ""
}
$"""

import json
import requests
from typing import Dict, List
import boto3
from datetime import timedelta
import random
import os
import string


def download_json(url: str) -> List[Dict[str, int]]:
    response = requests.get(url)
    data = response.json()
    return data

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

def deciseconds_to_time_format(ds: int) -> str:
    ms = int(ds / 10000)  # converting deciseconds to milliseconds
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time_string = f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    return time_string


punctuation = '。，、？！；：“”‘’【】()《》「」.,?!;:(){}[]<>'
strong_punctuation = ['.', '?', '!', '。',  '?', '!']
def generate_srt(subtitles: List[Dict[str, int]], min_length: int) -> str:
    srt_string = ""
    index = 1
    while subtitles:
        # Pop the first subtitle off the list
        subtitle = subtitles.pop(0)
        # Store the start and end time
        start_time = deciseconds_to_time_format(subtitle["start_time"])
        end_time = deciseconds_to_time_format(subtitle["end_time"])
        # Combine the sentences until the length is at least min_length
        combined_sentence = subtitle['sentence']
        while len(combined_sentence.split()) < min_length and subtitles:
            if combined_sentence.replace(' ', '')[-1] in strong_punctuation:
                break
            next_subtitle = subtitles.pop(0)
            end_time = deciseconds_to_time_format(next_subtitle["end_time"]) # update end time
            combined_sentence += ' ' + next_subtitle['sentence']
        # Remove trailing punctuation
        while combined_sentence[-1] in punctuation:
            combined_sentence = combined_sentence[:-1]
        # Add to the SRT string
        srt_string += f"{index}\n{start_time} --> {end_time}\n{combined_sentence}\n\n"
        index += 1
    return srt_string


def mindsflow_function(event, context) -> dict:
    # get the s3 bucket, file_name, and url from the event
    url = event.get("sentences_json_url")
    min_words_sentence = event.get("min_words_sentence", 5)

    # download the json from the url
    subtitles_json = download_json(url)

    # generate the srt from the json
    srt_data = generate_srt(subtitles_json, min_words_sentence)

    file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    file_name_srt = file_name + '.srt'
    with open(file_name_srt, 'w') as file:
        file.write(srt_data )
    srt_url = upload_to_aws(file_name_srt)
    os.remove(file_name_srt)

    print(srt_data)

    # define result
    result = {
        'srt_url': srt_url,
    }

    return result

        