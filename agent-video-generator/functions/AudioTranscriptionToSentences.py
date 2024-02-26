"""$
{
    "name": "AudioTranscriptionToSentences",
    "displayName": "",
    "description": "This method downloads a JSON file containing the transcription of an audio, including the start and duration of each word. It further splits the transcription into sentences and uses the JSON transcription to map the start and duration of each sentence.",
    "inputPattern": {
        "type": "object",
        "properties": {
            "add_punctuation": {
                "type": "boolean",
                "description": ""
            },
            "split_all_punctuation": {
                "type": "boolean",
                "description": ""
            },
            "transcription_json_url": {
                "type": "string",
                "description": "URL from where to download the json file."
            }
        },
        "required": [
            "split_all_punctuation",
            "transcription_json_url"
        ]
    },
    "outputPattern": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": ""
            },
            "n_splits": {
                "type": "number",
                "description": ""
            },
            "sentences_json_url": {
                "type": "string",
                "description": "URL to download JSON"
            }
        },
        "required": [
            "text",
            "n_splits",
            "sentences_json_url"
        ]
    },
    "tag": "DataPreprocessing",
    "testCases": [
        {
            "add_punctuation": false,
            "split_all_punctuation": false,
            "transcription_json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/audio_transcription_1703468432_yelpditk.json"
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import requests
import boto3
import time
import random
import string
import os
import nltk
import jieba
import re
import regex

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


light_punctuation = [',', "，"]


def divide_string(words, words2, split_all_punctuation=True):
    substrings = []
    substrings2 = []
    substring_len = []

    current_substring = ""
    current_substring2 = ""
    cur_substring_len = 0

    punctuation = [".", "!", "?", ";", "。", "！", "？", "；"]
    if split_all_punctuation is True:
        punctuation += light_punctuation
    for i, word in enumerate(words):
        if word[-1] in punctuation:
            #print(word, current_substring)
            cur_substring_len += 1
            if regex.match(r'\p{Script=Han}', word):
                current_substring += "" + word
                current_substring2 += "" + words2[i]
            else:
                current_substring += " " + word
                current_substring2 += " " + words2[i]
            substrings.append(current_substring.strip())
            substrings2.append(current_substring2.strip())
            current_substring = ""
            current_substring2 = ""
            substring_len.append(cur_substring_len)
            cur_substring_len = 0
        else:
            cur_substring_len += 1
            if regex.match(r'\p{Script=Han}', word):
                current_substring += "" + word
                current_substring2 += "" + words2[i]
            else:
                current_substring += " " + word
                current_substring2 += " " + words2[i]

    if current_substring: # If there's anything left, append it to the list
        substrings.append(current_substring.strip())
        substrings2.append(current_substring2.strip())
        substring_len.append(cur_substring_len)

    return substrings, substrings2, substring_len

llm_prompt = '''split this text into smaller sentences
TEXT: {}'''
def llm_add_puntuaction(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": llm_prompt.format(input_str),
        "agentId": 964
    }
    resp = event.chat.messages(data=data)
    return resp

def get_sentence_time(json_file_path, event, split_all_punctuation=True, add_punctuation=False):
    # Load JSON data from a file
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    # Get display text and split into sentences
    display_lexical = data['Lexical'].strip()
    display_text = data['Display'].strip().replace('.', '. ')

    if add_punctuation:
        display_text = llm_add_puntuaction(display_text, event) # to test

    lexical_list = display_lexical.split()
    text_list = display_text.split()
    print(len(lexical_list), lexical_list)
    print(len(text_list), text_list)

    def n_split_str(str_, n):
        words = str_.split()
        return [' '.join(words[i:i+n]) for i in range(0, len(words), n)]
    def count_words(sentences):
        return [len(sentence.split()) for sentence in sentences]

    if len(lexical_list) != len(text_list):
        sentences_text = n_split_str(display_lexical, 10)
        sentences_clean = sentences_text
        substring_len_text  = count_words(sentences_text)
        substring_len_lexical = substring_len_text
    else:
        sentences_text, sentences_clean, substring_len_text = divide_string(text_list, lexical_list, split_all_punctuation)
        substring_len_lexical = substring_len_text

    print(sentences_clean)
    print(substring_len_text ,sentences_text)

    # Map words to their times
    words = [{'Word': w['Word'], 'Index': index, 'Offset': w['Offset'], 'Duration': w['Duration']} for index, w in enumerate(data['Words'])]
    #print(words)

    sentence_times = []

    index = 0
    for i, sentence in enumerate(sentences_text):
        start_time = words[index]['Offset']
        index += substring_len_lexical[i] - 1
        end_time = words[index]['Offset'] + words[index]['Duration']
        duration = end_time - start_time
        index += 1
        #print(duration)
        final_sentence = sentences_text[i]
        while final_sentence[-1] in light_punctuation:
            final_sentence = final_sentence[:-1]

        sentence_times.append({
            'sentence': final_sentence,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        })

    return sentence_times, display_text


def mindsflow_function(event, context) -> dict:
    
    url = event.get('transcription_json_url')
    split_all_punctuation = event.get('split_all_punctuation', True)
    add_punctuation = event.get('add_punctuation', False)
    
    transcription_path = 'transcript_{}.json'.format(get_random_string())
    download_file(url, transcription_path)

    sentence_times, text = get_sentence_time(transcription_path, event, split_all_punctuation, add_punctuation)

    output_file = 'sentence_times_{}.json'.format(get_random_string())
    with open(output_file, 'w') as f:
        json.dump(sentence_times, f)

    url = upload_to_aws(output_file)

    result = {
        'sentences_json_url': url,
        'text': text,
        'n_splits': len(sentence_times)
    }

    if os.path.exists(transcription_path):
        os.remove(transcription_path)
    if os.path.exists(output_file):
        os.remove(output_file)

    return result

        