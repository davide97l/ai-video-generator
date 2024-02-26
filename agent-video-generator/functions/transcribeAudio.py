"""$
{
    "name": "transcribeAudio",
    "displayName": "",
    "description": "This method transcribes audio into text using Azure API, maps start time and duration for each word, converts the transcription to JSON format, and uploads the resulting file to AWS S3. Its input is an audio file.",
    "inputPattern": {
        "type": "object",
        "properties": {
            "lang": {
                "type": "string",
                "description": ""
            },
            "audio_url": {
                "type": "string",
                "description": "URL string of the audio to be transcribed"
            }
        },
        "required": [
            "audio_url"
        ]
    },
    "outputPattern": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": ""
            },
            "duration": {
                "type": "number",
                "description": ""
            },
            "transcription_json_url": {
                "type": "string",
                "description": "The transcription results from the audio file"
            }
        },
        "required": [
            "text",
            "duration",
            "transcription_json_url"
        ]
    },
    "tag": "TextToSpeech",
    "testCases": [
        {
            "lang": "en",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/audio_20231226132719.wav"
        },
        {
            "lang": "en",
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/tony_stark.wav"
        }
    ],
    "aiPrompt": "This method is designed to transcribe audio using the Azure API, get the start time and duration of each word, convert the output to JSON format, and then upload the resulting file to AWS S3. The input for this process is an audio file",
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
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
import azure.cognitiveservices.speech as speechsdk
from pydub.utils import mediainfo


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


def modify_last_word(input_string):
    # Remove any trailing whitespace
    input_string = input_string.strip()

    if input_string.endswith(','):
        # Replace the last character with a period
        input_string = input_string[:-1] + '.'
    # Check if the last word ends with a period
    if not input_string.endswith('.'):
        # Add a period at the end if the last word doesn't end with one
        input_string += '.'

    return input_string


def add_punctuation(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 1605
    }
    resp = event.chat.messages(data=data)
    return resp


def fix_punctuation(a_string: str, b_string: str) -> str:
    i_a = 0
    i_b = 0
    while i_a < len(a_string) - 1 and i_b < len(b_string) - 1:
        while b_string[i_b] in [',', '.', '!', '?']:
            i_b += 1
        if a_string[i_a] != ' ' and a_string[i_a + 1] != ' ' and b_string[i_b] == a_string[i_a] and (b_string[i_b+1:i_b+3] == ', ' or b_string[i_b+1:i_b+2] == ',') and b_string[i_b+3] == a_string[i_a + 1]:
            print('a')
            b_string = b_string[:i_b+1] + b_string[i_b+3:]
        i_a += 1
        i_b += 1
    return b_string


def transcribe_audio(audio_path: str, lang: str, event) -> dict:
    final_results = {'Display': '', 'Lexical': '', 'Words': [], 'Duration': 0}
    done = False
    audio_info = mediainfo(audio_path)
    total_duration = int(float(audio_info["duration"]) * 1e7)  # convert seconds to 100-nanosecond units
    print('duration:', total_duration)
    final_results['Duration'] = total_duration

    def recognized_cb(evt):
        """callback that is called when a piece of speech is recognized"""
        print('RECOGNIZED: {}'.format(evt))
        nonlocal final_results
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            json_result = json.loads(evt.result.json)

            lexical = json_result["NBest"][0]['Lexical'].split()
            display = json_result["NBest"][0]['Display'].split()
            lexical= [element for element in lexical if not element.startswith("'")]
            #print('L', len(lexical), lexical)
            #print('D',len(display), display)

            words = []
            lexical_list = []
            #display_list = []
            best_words = json_result["NBest"][0]['Words']
            #print('B', best_words)
            i = 0
            for item in best_words:
                if "'" in item['Word']:
                    print('skip:', item['Word'])
                    continue
                if (best_words[i]['Offset']) +best_words[i]['Duration'] / 2  <= total_duration:
                    words.append(best_words[i])
                    lexical_list.append(lexical[i])
                    #display_list.append(display[i])
                    #print(lexical[i], best_words[i]['Word'], best_words[i]['Offset'])
                    i += 1
            #print(i, len(best_words))
            while i < len(best_words) and (best_words[i]['Offset'] +best_words[i]['Duration'] / 2 ) <= total_duration:
                if i>= len(lexical):
                    #print('DEBUG:', i, len(lexical), len(best_words))
                    #print('DEBUG: exit cycle')
                    break
                words.append(best_words[i])
                lexical_list.append(lexical[i])
                #display_list.append(display[i])
                #print(display[i], lexical[i], best_words[i]['Word'], best_words[i]['Offset'])
                i += 1

            #print('end record duration')
            #print(display[i], lexical[i], best_words[i]['Word'], best_words[i]['Offset'])
            lexical = ' '.join(lexical_list).strip()
            #display = ' '.join(display_list).strip()
            #print('update results')
            final_results['Words'] += words
            final_results['Lexical'] += lexical.strip() + ' '
            #final_results['Display'] += display.strip() + ' '
            #print(final_results['Lexical'] )

    def stop_cb(evt):
        """callback that stops continuous recognition on receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    # your Azure Speech service configuration
    speech_key = os.environ.get('azure_key')
    service_region = os.environ.get('azure_region')
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.request_word_level_timestamps()
    lang_dict = {
        'en': 'en-US',
        'ch': 'zh-CN',
        'zh': 'zh-CN',
        'it': 'it-IT',
        'de': 'de-DE',
        'fr': 'fr-FR',
        'es': 'es-ES'
    }
    speech_config.speech_recognition_language = lang_dict[lang] 
    #speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "1000")

    # specifying audio file path
    audio_input = speechsdk.AudioConfig(filename=audio_path)

    # creating a speech recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # perform continuous recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)
    
    final_results['Display'] = add_punctuation(final_results['Lexical'], event).strip().replace('//', '').replace('"', '')
    final_results['Display'] = fix_punctuation(final_results['Lexical'], final_results['Display'])
    print(len(final_results['Display'].split()), len(final_results['Lexical'].split()))
    #final_results['Display'] = modify_last_word(final_results['Display'])
    return final_results


def mindsflow_function(event, context) -> dict:
    # get the audio url from the event
    audio_url = event.get("audio_url")
    lang = event.get("lang", "en")
    
    # download the audio file
    audio_file = requests.get(audio_url)
    
    audio_path = audio_url.split('/')[-1]
    with open(audio_path, 'wb') as f: 
        f.write(audio_file.content)

    # get the Transcription result
    transcription_result = transcribe_audio(audio_path, lang, event)

    transcription_path = 'audio_transcription_{}.json'.format(get_random_string())
    # upload transcription result to S3
    with open(transcription_path, 'w') as f:
        json.dump(transcription_result, f)
        
    url = upload_to_aws(transcription_path)

    # prepare the result
    result = {
        'transcription_json_url': url,
        'duration': transcription_result['Duration'],
        'text': transcription_result['Display']
    }

    if os.path.exists(transcription_path):
        os.remove(transcription_path)

    return result

        