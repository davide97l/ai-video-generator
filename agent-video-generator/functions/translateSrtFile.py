"""$
{
    "name": "translateSrtFile",
    "displayName": "",
    "description": "This method downloads a subtitle file from a provided URL, translates it into a specified target language while keeping the original language, uploads the translated file to S3, and removes it from the local system.",
    "inputPattern": {
        "type": "object",
        "required": [
            "srt_url",
            "source_lang",
            "target_lang",
            "show_source_lang_captions",
            "show_target_lang_captions"
        ],
        "properties": {
            "srt_url": {
                "type": "string",
                "description": "URL of the SRT file to be translated"
            },
            "source_lang": {
                "type": "string",
                "description": "The language of the original SRT file"
            },
            "target_lang": {
                "type": "string",
                "description": "The language to translate the SRT file into"
            },
            "captions_line": {
                "type": "integer",
                "description": ""
            },
            "show_source_lang_captions": {
                "type": "boolean",
                "description": ""
            },
            "show_target_lang_captions": {
                "type": "boolean",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "transl_srt_url"
        ],
        "properties": {
            "transl_srt_url": {
                "type": "string",
                "description": "The S3 bucket path where the translated file is uploaded"
            }
        }
    },
    "tag": "VideoCaptions",
    "testCases": [
        {
            "srt_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/01w5zy.srt",
            "source_lang": "it",
            "target_lang": "ch",
            "captions_line": 15,
            "show_source_lang_captions": true,
            "show_target_lang_captions": false
        },
        {
            "srt_url": "",
            "source_lang": "",
            "target_lang": "de",
            "captions_line": 0,
            "show_source_lang_captions": false,
            "show_target_lang_captions": false
        }
    ],
    "aiPrompt": "Given the url of a srt file, download it and translate subtitle to a target language. The final srt file must contain subtitles in both languages. Input include also original and target language. Finally upload the file to s3 and remote if from local.",
    "greeting": ""
}
$"""

import json
import boto3
import requests
from googletrans import Translator
from pysrt import open as open_srt
import random
import os
import string


def download_file(url: str, local_path: str) -> bool:
    r = requests.get(url, allow_redirects=True)
    open(local_path, 'wb').write(r.content)
    return True


def translate_text(input_file_path: str, output_file_path: str, origin_lang: str, target_lang: str) -> str:
    translator = Translator()
    srt_file = open_srt(input_file_path)
    for line in srt_file:
        translated_text = translator.translate(line.text, src=origin_lang, dest=target_lang)
        line.text += "\n" + translated_text.text
    srt_file.save(output_file_path, encoding='utf-8')
    return True

def split_text(input_file_path, output_file_path: str, source_lang: str, target_lang: str, new_line_after: int = 15, show_target_lang_captions = True, show_source_lang_captions = True) -> bool:
    srt_file = open_srt(input_file_path)
    for line in srt_file:
        source_text, trans_text = line.text.split("\n")
        if "chinese" in target_lang or "japanese" in target_lang:
            trans_text = '\n'.join(trans_text[i:min(i+new_line_after, len(trans_text))] for i in range(0, len(trans_text), new_line_after))
        if "chinese" in source_lang or "japanese" in source_lang:
            source_text = '\n'.join(source_text[i:min(i+new_line_after, len(source_text))] for i in range(0, len(source_text), new_line_after))
        if show_source_lang_captions is False and show_target_lang_captions is True:
            line.text = trans_text
        elif show_target_lang_captions is False and show_source_lang_captions is True:
            line.text = source_text
        else:
            line.text = source_text + "\n" + trans_text
    srt_file.save(output_file_path, encoding='utf-8')
    return True


llm_prompt = '''Given the input sentence in {}, correct any logical, semantic or spelling mistake. If possible also summarize the correctd sentence. Return only the correct sentence. 
SENTENCE: {}
CORRECT SENTENCE: '''
def fix_text(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 964
    }
    resp = event.chat.messages(data=data)
    return resp


def fix_srt_file(input_file_path: str, origin_lang: str, event) -> bool:
    srt_file = open_srt(input_file_path)
    for line in srt_file:
        temp_prompt = llm_prompt.format(origin_lang, line.text)
        fixed_text = fix_text(temp_prompt, event)
        #print(line.text, fixed_text)
        line.text = fixed_text
    srt_file.save(input_file_path, encoding='utf-8')
    return True


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

def remove_file(local_path: str):
    os.remove(local_path)


def mindsflow_function(event, context) -> dict:
    srt_file_url = event.get("srt_url")
    src_lang = event.get("source_lang")
    tgt_lang = event.get("target_lang")
    captions_line = event.get("captions_line", 15)
    show_target_lang_captions  = event.get("show_target_lang_captions", True)
    show_source_lang_captions = event.get("show_source_lang_captions", True)

    input_file_path = "input_file.srt"
    random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    output_file_path = random_string + "output_file.srt"
    
    download_file(srt_file_url, input_file_path)

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
    if src_lang in lang_dict.keys():
        src_lang = lang_dict[src_lang]
    if tgt_lang in lang_dict.keys():
        tgt_lang = lang_dict[tgt_lang]

    #fix_srt_file(input_file_path, src_lang, event)
    
    translate_text(input_file_path, input_file_path, src_lang, tgt_lang)
    split_text(input_file_path, output_file_path, src_lang, tgt_lang, new_line_after=captions_line, show_target_lang_captions=show_target_lang_captions,
    show_source_lang_captions=show_source_lang_captions)

    trans_srt_url = upload_to_aws(output_file_path)

    remove_file(input_file_path)
    remove_file(output_file_path)

    result = {
        'transl_srt_url': trans_srt_url
    }

    return result

        