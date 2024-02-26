"""$
{
    "name": "preprocessTrainData",
    "displayName": "",
    "description": "This function downloads an audio file, transforms it into a wav format, and then uploads it to a specified data storage bucket.",
    "inputPattern": {
        "type": "object",
        "required": [
            "audio_url"
        ],
        "properties": {
            "voice": {
                "type": "string",
                "description": ""
            },
            "make_zip": {
                "type": "boolean",
                "description": ""
            },
            "audio_url": {
                "type": "string",
                "description": "URL of the file to be downloaded and converted"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "audio_url"
        ],
        "properties": {
            "audio_url": {
                "type": "string",
                "description": "url of the converted file"
            }
        }
    },
    "tag": "VoiceCloning",
    "testCases": [
        {
            "voice": "hhh",
            "make_zip": true,
            "audio_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/transfer/chinese_poadcast_woman1.m4a"
        },
        {
            "voice": "",
            "make_zip": false,
            "audio_url": ""
        }
    ],
    "aiPrompt": "Cloning voice...",
    "greeting": ""
}
$"""

import os
import json
import requests
from pydub import AudioSegment
import boto3
import zipfile
import glob
import shutil
from datetime import datetime

def download_file(url: str) -> str:
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return local_filename

def convert_audio_to_wav(file_path: str) -> str:
    audio = AudioSegment.from_file(file_path)
    wav_filename = os.path.splitext(file_path)[0] + '.wav'
    audio.export(wav_filename, format="wav")
    return wav_filename

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

    bucket_path = 'temp_audio'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    
    return url

def zip_wav_file(wav_file_path):
    # Check if file exists
    if not os.path.isfile(wav_file_path):
        print("File does not exist at provided path.")
        return

    # Extracting directory path, file name and file base name
    dir_path, file_name = os.path.split(wav_file_path)
    file_base_name, _ = os.path.splitext(file_name)

    # Creating new directory with same name as the wav file
    new_dir_path = os.path.join(dir_path, file_base_name)

    # If the directory already exists, append a timestamp to its name
    #if os.path.exists(new_dir_path):
    #    timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
    #    new_dir_path += timestamp

    os.makedirs(new_dir_path, exist_ok=True)

    # Moving the wav file to the new directory
    shutil.move(wav_file_path, os.path.join(new_dir_path, file_name))
   
    # Creating a zip file and adding the directory with the wav file in it
    # If the zip file already exists, append a timestamp to its name
    zip_file_path = dir_path + '/' + file_base_name + '.zip'
    if os.path.isfile(zip_file_path):
      zip_file_path = os.path.splitext(zip_file_path)[0] + ".zip"

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(new_dir_path):
                for filename in filenames:
                    # create complete filepath of file in directory
                    file_to_zip = os.path.join(foldername, filename)
                    # add file to zip
                    zipf.write(file_to_zip, os.path.relpath(file_to_zip, dir_path))

    print(f"Zip file saved at: {zip_file_path}")
    return zip_file_path

def mindsflow_function(event, context) -> dict:
    # get params from the event
    url = event.get("audio_url")
    make_zip = event.get("make_zip", False)
    voice = event.get("voice", None)
    ext = url.split('.')[-1]
    if ext in [ 'zip']:
        return {
            'audio_url': url
    }
    if ext in [ 'wav'] and make_zip is False:
        return {
            'audio_url': url
    }
    
    # Download file
    local_filename = download_file(url)
    if voice is not None:
        new_filename = f'{voice}.wav'
        shutil.move(local_filename, new_filename)
        local_filename = new_filename
    
    # Convert audio to wav
    wav_filename = convert_audio_to_wav(local_filename)

    if make_zip:  # TODo chasnge file nasme
        wav_filename = zip_wav_file(wav_filename)
        if voice is not None:
            new_filename = f'{voice}.zip'
            shutil.move(wav_filename, new_filename)
            wav_filename = new_filename
    
    # Upload wav file to S3 bucket
    response = upload_to_aws(wav_filename)

    files = glob.glob('./*.zip') +  glob.glob('./*.wav') + glob.glob('./*.m4a') + glob.glob('./*.mp3')
    for file_name in files:
        try:
            os.remove(file_name)
            print('File ', file_name ,'removed successfully.')
        except:
            print('Error while deleting file ', file_name)
    
    # define result
    result = {
        'audio_url': response
    }
    
    return result

        