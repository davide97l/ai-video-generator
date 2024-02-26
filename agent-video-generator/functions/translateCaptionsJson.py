"""$
{
    "name": "translateCaptionsJson",
    "displayName": "",
    "description": "Translate captions in json file",
    "inputPattern": {
        "type": "object",
        "required": [
            "json_url",
            "source_language",
            "target_language"
        ],
        "properties": {
            "json_url": {
                "type": "string",
                "description": ""
            },
            "source_language": {
                "type": "string",
                "description": ""
            },
            "target_language": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "json_url"
        ],
        "properties": {
            "json_url": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "Translation",
    "testCases": [
        {
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/sentence_times_1699866757_slkpxpcq.json",
            "source_language": "en",
            "target_language": "it"
        },
        {
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/sentence_times_1700135459_xyxdjgbl.json",
            "source_language": "zh",
            "target_language": "en"
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
from googletrans import Translator, LANGUAGES
import os
import boto3
import requests
import shutil
import random
import string
import pydub


def download_file(url, filename):
    res = requests.get(url)
    with open(filename, "wb") as f:
        f.write(res.content)


def upload_to_aws(filename: str) -> str:
    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    s3_client = session.client('s3')
    bucket_path = 'temp_audio'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    return url


def get_captions_from_url(url):
    filename = f"{url.split('/')[-1]}"
    # download the json file
    download_file(url, filename)
    # read the contents
    with open(filename, 'r', encoding='utf-8') as f:
        captions = json.load(f)
    return captions, filename


def translate_text(text, source_language, target_language):
    translator = Translator()
    lang_dict = {
        'en': 'english',
        'zh': 'chinese (simplified)',
        'ch': 'chinese (simplified)',
        'de': 'german',
        'ge': 'german',
        'it': 'italian',
        'fr': 'french',
        'sp': 'spanish',
        'es': 'spanish',
    }
    source_language = lang_dict[source_language]
    target_language = lang_dict[target_language]
    #print(source_language, target_language)
    #print(LANGUAGES.values())
    if source_language not in LANGUAGES.values() or target_language not in LANGUAGES.values():
        return "Invalid source or target language."
    translation = translator.translate(text, src=source_language, dest=target_language)
    return translation.text


# make this func indepenednt
def translate_captions(captions, source_language, target_language):
    translated_captions = []
    for cap in captions:
        cap['translation'] = translate_text(cap['sentence'], source_language, target_language)
        translated_captions.append(cap)
    return translated_captions


def mindsflow_function(event, context) -> dict:
    json_url = event.get("json_url")
    target_language = event.get("target_language")
    source_language = event.get("source_language")

    # download and read the captions from the json file
    captions, json_file = get_captions_from_url(json_url)
    # add translated sentences into the target language
    translated_captions = translate_captions(captions, source_language, target_language)

    translated_json = 'translated' + ''.join(random.choice(string.ascii_letters) for _ in range(6)) + '.json'
    with open(translated_json, 'w', encoding='utf8') as f:
        json.dump(translated_captions, f, ensure_ascii=False, indent=4)
    json_url = upload_to_aws(translated_json)
    os.remove(translated_json)

    return {'json_url': json_url}

        