"""$
{
    "name": "generateAudioSegmentsFromJson",
    "displayName": "",
    "description": "Generate audio from json captions.",
    "inputPattern": {
        "type": "object",
        "required": [
            "json_url",
            "target_lang"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": ""
            },
            "json_url": {
                "type": "string",
                "description": "URL of the JSON file containing captions"
            },
            "target_lang": {
                "type": "string",
                "description": "The language into which the captions should be translated"
            },
            "enhance_sync": {
                "type": "boolean",
                "description": ""
            },
            "max_speech_rate": {
                "type": "number",
                "description": ""
            },
            "min_speech_rate": {
                "type": "number",
                "description": ""
            },
            "summarize_long_sentences": {
                "type": "boolean",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "translation_folder"
        ],
        "properties": {
            "translation_folder": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "TextToSpeech",
    "testCases": [
        {
            "voice": "zh-CN-male",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedVceeOp.json",
            "target_lang": "zh",
            "enhance_sync": false,
            "max_speech_rate": 1.5,
            "min_speech_rate": 0.5,
            "summarize_long_sentences": false
        },
        {
            "voice": "it-IT': 'Microsoft Server Speech Text to Speech Voice (it-IT, ElsaNeural)",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedAOjUGH.json",
            "target_lang": "it",
            "enhance_sync": false,
            "max_speech_rate": 0,
            "min_speech_rate": 0,
            "summarize_long_sentences": false
        },
        {
            "voice": "zh-CN-YunfengNeural",
            "json_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/temp_audio/translatedDLYYSi.json",
            "target_lang": "zh",
            "enhance_sync": true,
            "max_speech_rate": 0,
            "min_speech_rate": 0,
            "summarize_long_sentences": false
        }
    ],
    "aiPrompt": "Is given the URL of a json file containing a set of captions and their start and duration in a video. download the file and read the content. Translate each sentence into a target language. Then generate the audio of each translated sentence. Is also given the URl of the video. download it and add each audio segment back to the video according to its start time",
    "greeting": ""
}
$"""

import json
import os
import boto3
import requests
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer, SpeechSynthesisOutputFormat
import langid
langid.set_languages(['en', 'zh', 'ja'])
import shutil
import random
import string
import pydub


time_unit = 10000000


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


def calculate_element_count(text):
    chinese_punctuations = "！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏."
    text = text.translate(str.maketrans('', '', string.punctuation + chinese_punctuations))
    # Consider language specifics (ex: Chinese is rather based on characters)
    if langid.classify(text)[0] in ['zh', 'ja']:
        return len(text.replace(' ', ''))  # Spaces are not typically considered in character count
    else:
        return len(text.split())


def calculate_speech_rate(text, duration):
    element_count = calculate_element_count(text)
    #print('Element count:', element_count)
    #print('Duration:', duration)
    duration_in_seconds = float(duration) / float(time_unit)
    #print('Duration in seconds', duration_in_seconds)
    speech_rate = element_count / float(duration_in_seconds) * 60.
    return speech_rate, element_count

llm_prompt = 'Shorten the input text. The output must have less words than the input. Keep the original language.\n INPUT: {}.\n OUTPUT:'
def summarize_text(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 964
    }
    resp = event.chat.messages(data=data)
    return resp

lang_dict = {
    'en': 'en-US',
    'zh': 'zh-CN',
    'ch': 'zh-CN',
    'de': 'de-DE',
    'ge': 'de-DE',
    'it': 'it-IT',
    'fr': 'fr-FR',
    'sp': 'es-ES',
    'es': 'es-ES',
}

speaker_dict = {
    'en-US': 'Microsoft Server Speech Text to Speech Voice (en-US, Jessa24kRUS)',
    'zh-CN': 'Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)',
    'it-IT': 'Microsoft Server Speech Text to Speech Voice (it-IT, ElsaNeural)',
    'de-DE': 'Microsoft Server Speech Text to Speech Voice (de-DE, KatjaNeural)',
    'fr-FR': 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)',
    'es-ES': 'Microsoft Server Speech Text to Speech Voice (es-ES, ElviraNeural)',

    'zh-CN-male': 'zh-CN-YunfengNeural',
    'zh-CN-female': 'zh-CN-XiaomengNeural',
}

speech_rate_dict = {
    'en-US': 150,
    'zh-CN': 400,
}


def generate_audio(captions, lang: str = 'en', translation_folder: str = 'translation_folder', enhance_sync: bool = True, event = None, voice=None, summarize_long_sentences=False, min_speech_rate=0.5, max_speech_rate=1.5):
    if lang in lang_dict.keys():
        lang = lang_dict[lang]
    if 'male' in voice or 'female' in voice:
        speaker = speaker_dict[voice]
    elif lang in voice:
        speaker = voice
    else:
        speaker = speaker_dict[lang]
    print('Using speaker:', speaker)

    filename = '{}/audio_segment_{}.wav'
    speech_key = os.environ.get('azure_key')
    service_region = os.environ.get('azure_region')
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    tot_error = []
    for i, cap in enumerate(captions):
        temp_filename = filename.format(translation_folder, str(i+1))
        audio_output = speechsdk.audio.AudioOutputConfig(filename=temp_filename)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
        text = cap['translation']
        duration = cap['duration']
        original_text = cap['sentence']
        #voice_speed = (speech_rate / ai_speech_rate)
        print(i+1, text, original_text)
        voice_speed = 1.
        #break
        if voice_speed != 1.0 and voice_speed != 1:
            voice_speed = int(voice_speed * 100.0 - 100.0)
            text = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'><voice name='{speaker}'><prosody rate='{voice_speed}.00%'>" + text + "</prosody></voice></speak>"
        else:
            text = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'><voice name='{speaker}'>" + text + "</voice></speak>"

        result = speech_synthesizer.speak_ssml_async(text).get()
        stream = AudioDataStream(result)
        stream.save_to_wav_file(temp_filename)

        # Get the duration of the audio file
        audio = pydub.AudioSegment.from_file(temp_filename)
        duration = audio.duration_seconds

        speech_rate_min, speech_rate_max = min_speech_rate, max_speech_rate
        if enhance_sync:
            text = cap['translation']
            dur_diff_rate = duration / (cap['duration'] / time_unit)
            print('Duration diff rate', dur_diff_rate)
            if summarize_long_sentences is True and  dur_diff_rate > speech_rate_max and len(text) >= 3:  # when translated audio is too long
                prev_text = text
                text = summarize_text(llm_prompt.format(text), event)
                print(f"Translated text is too long: {cap['duration']}s vs {duration}s. Rewording: {prev_text} -> {text} ")
            prev_duration = duration
            err = abs(duration-cap['duration'] / time_unit)
            print('Before synch', prev_duration, cap['duration'] / time_unit, err)
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
            temp_filename = filename.format(translation_folder, str(i+1))
            audio_output = speechsdk.audio.AudioOutputConfig(filename=temp_filename)
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
            voice_speed = duration / (cap['duration'] / time_unit)
            min_speed, max_speed = speech_rate_min, speech_rate_max
            voice_speed = min(max_speed, max(min_speed, voice_speed))
            voice_speed = int(voice_speed * 100.0 - 100.0)
            text = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'><voice name='{speaker}'><prosody rate='{voice_speed}.00%'>" + text + "</prosody></voice></speak>"
            result = speech_synthesizer.speak_ssml_async(text).get()
            stream = AudioDataStream(result)
            stream.save_to_wav_file(temp_filename)
            # Get the duration of the audio file
            audio = pydub.AudioSegment.from_file(temp_filename)
            duration = audio.duration_seconds

        err = abs(duration-cap['duration'] / time_unit)
        print('After synch', duration, cap['duration'] / time_unit, err)
        tot_error.append(err)
    print('Total mismatch:', sum(tot_error) / len(tot_error))

    return filename


def mindsflow_function(event, context) -> dict:
    json_url = event.get("json_url")
    target_language = event.get("target_lang")
    enhance_sync = event.get("enhance_sync", False)
    summarize_long_sentences = event.get("summarize_long_sentences", None)
    voice = event.get("voice", None)
    min_speech_rate = event.get("min_speech_rate", 0.5)
    max_speech_rate = event.get("max_speech_rate", 1.5)

    if voice is not None and voice.lower() in ['none']:
        voice = None

    audio_folder = 'audio_folder_' + ''.join(random.choice(string.ascii_letters) for _ in range(6))  # make static name for debug
    if os.path.exists(audio_folder):
        shutil.rmtree(audio_folder)
    os.makedirs(audio_folder)

    # download and read the captions from the json file
    captions, _ = get_captions_from_url(json_url)
    # generate audios from the translated captions
    generate_audio(captions, target_language, audio_folder, enhance_sync, event, voice, summarize_long_sentences, min_speech_rate, max_speech_rate)

    return {'audio_folder': audio_folder}
        