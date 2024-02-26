"""$
{
    "name": "textToSpeech",
    "displayName": "",
    "description": "This Python method converts a text string into audio. The URL of the resulting audio is then returned.",
    "inputPattern": {
        "type": "object",
        "required": [
            "text"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert into voice"
            },
            "speaker": {
                "type": "string",
                "description": "speaker"
            },
            "language": {
                "type": "string",
                "description": "Voice language"
            },
            "voice_speed": {
                "type": "number",
                "description": "voice speed"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "duration",
            "audio_url"
        ],
        "properties": {
            "duration": {
                "type": "number",
                "description": ""
            },
            "audio_url": {
                "type": "string",
                "description": "URL address of the generated voice"
            }
        }
    },
    "tag": "TextToSpeech",
    "testCases": [
        {
            "text": "Hi, my name is Hello world",
            "speaker": "en-US-GuyNeural",
            "language": "en",
            "voice_speed": 1
        },
        {
            "text": "What is the weather today?",
            "speaker": "",
            "language": "en",
            "voice_speed": 1
        },
        {
            "text": "Mi piace mangiare la pasta",
            "speaker": "",
            "language": "it",
            "voice_speed": 1
        }
    ],
    "aiPrompt": "The method converts a given text string into audio. If a sample voice is provided, the generated audio is created by cloning the sample voice. The URL address of the generated voice is returned.",
    "greeting": ""
}
$"""

import os
import boto3
import datetime
import requests
from pydub import AudioSegment
import pydub
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer, SpeechSynthesisOutputFormat

def download_file(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    file_extension = url.split(".")[-1].lower()
    if file_extension == "mp3":  # Convert the MP3 file to WAV
        audio = AudioSegment.from_mp3(save_path)
        audio.export(save_path, format="wav")
        return save_path
    elif file_extension == "wav":
        return save_path
    else:
        raise Exception("Unsupported file format. Only MP3 and WAV files are supported.")

lang_dict = {
        'en': 'en-US',
        'ch': 'zh-CN',
        'zh': 'zh-CN',
        'it': 'it-IT',
        'de': 'de-DE',
        'fr': 'fr-FR',
        'es': 'es-ES'
 }

speaker_dict = {
    'en-US': 'Microsoft Server Speech Text to Speech Voice (en-US, Jessa24kRUS)',
    'zh-CN': 'Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)',
    'it-IT': 'Microsoft Server Speech Text to Speech Voice (it-IT, ElsaNeural)',
    'de-DE': 'Microsoft Server Speech Text to Speech Voice (de-DE, KatjaNeural)',
    'fr-FR': 'Microsoft Server Speech Text to Speech Voice (fr-FR, DeniseNeural)',
    'es-ES': 'Microsoft Server Speech Text to Speech Voice (es-ES, ElviraNeural)'
}

def generate_audio(text: str, lang: str = 'en', voice_speed: float = 1.0, speaker: str = None):
    if lang in lang_dict.keys():
        lang = lang_dict[lang]
    print('Setting lang:', lang)
    if speaker is None or speaker in ['none', '']:  # use default speaker
        speaker = speaker_dict[lang]
    print('Using speaker:', speaker)
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    filename = f'audio_{timestamp}.wav'
    speech_key = os.environ.get('azure_key')
    service_region = os.environ.get('azure_region')
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_output = speechsdk.audio.AudioOutputConfig(filename=filename)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)
    
    if voice_speed != 1.0 and voice_speed != 1:
        voice_speed = int(voice_speed * 100.0  - 100.0)
        text = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'><voice name='{speaker}'><prosody rate='{voice_speed}.00%'>" + text + "</prosody></voice></speak>"
    else:
        text = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'><voice name='{speaker}'>" + text + "</voice></speak>"
    result = speech_synthesizer.speak_ssml_async(text).get()
    stream = AudioDataStream(result)
    stream.save_to_wav_file(filename)
    
    # Get the duration of the audio file
    audio = pydub.AudioSegment.from_file(filename)
    duration = audio.duration_seconds

    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')

    # Create a session using the provided credentials
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )

    # Create an S3 client
    s3_client = session.client('s3')

    bucket_path = 'temp_audio'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    video_url = f'{s3_base_url}{bucket_path}/{filename}'

    os.remove(filename)

    return video_url, duration

def mindsflow_function(event, context) -> dict:
    # get the text and save path from the event
    text = event.get("text")
    lang = event.get("language", "en")
    voice_speed = event.get("voice_speed", None)
    speaker = event.get("speaker", None)
    
    # generate the audio file
    audio_url, duration = generate_audio(text, lang, voice_speed, speaker)

    # define result
    result = {
        'audio_url': audio_url,
        'duration': duration
    }

    return result

        