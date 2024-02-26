"""$
{
    "name": "generateVideoScript",
    "displayName": "",
    "description": "generate video script",
    "inputPattern": {
        "type": "object",
        "required": [
            "topic"
        ],
        "properties": {
            "topic": {
                "type": "string",
                "description": ""
            },
            "text_style": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "json_string"
        ],
        "properties": {
            "json_string": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "VideoGeneration",
    "testCases": [
        {
            "topic": "Benefits of eating mango",
            "text_style": "scientific, straight to the point, easy to read"
        },
        {
            "topic": "Story of two brothers, sci-fi",
            "text_style": ""
        },
        {
            "topic": "story, sci-fi, epic",
            "text_style": ""
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


def generate_story_prompt(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1601
    }
    resp = event.chat.messages(data=data)
    return resp

def generate_paragraph_prompt(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1599
    }
    resp = event.chat.messages(data=data)
    return resp

def generate_music_prompt(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1604
    }
    resp = event.chat.messages(data=data)
    return resp

prompt = 'Given a text style and a text, turn the text into that style\nTEXT: {}\nSTYLE: {}\nNEW TEXT: '
def personalize_text(text: str, style: str, event) -> str:
    input_str = prompt.format(text, style)
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1548
    }
    resp = event.chat.messages(data=data)
    return resp

def mindsflow_function(event, context) -> dict:
    topic = event.get("topic")
    style = event.get("text_style", None)
    return_url = event.get("return_url", True)
    if 'story' in topic or 'Story' in topic or 'STORY' in topic:
        json_string = generate_story_prompt(topic, event)
    else:
        json_string = generate_paragraph_prompt(topic, event)
    
    json_url = None
    #print(json_string)
    dict_object = json.loads(json_string.replace('\\', ''))

    music_prompt = generate_music_prompt(topic, event)
    dict_object['music_prompt'] = music_prompt.replace('//', '').replace('"', '')

    if style is not None:
        dict_object['original_text'] = dict_object['Text']
        dict_object['Text'] = personalize_text(dict_object['Text'], style, event)

    json_path = f"script_{uuid.uuid4()}.json"
    with open(json_path, 'w') as f:
        json.dump(dict_object, f)
    json_url = upload_to_aws(json_path)
    os.remove(json_path)

    result = {
        'json_string': json_string,
        'json_url': json_url
    }
    # iterates over each key-value pair in the JSON object
    for key, value in dict_object.items():
        result[key.lower()] = value

    return result

        