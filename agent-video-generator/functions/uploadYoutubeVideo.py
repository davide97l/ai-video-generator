"""$
{
    "name": "uploadYoutubeVideo",
    "displayName": "",
    "description": "Manages the process of uploading a video to YouTube inclusive of its URL, title, description, and category, after which it deletes the video and returns a success status. The YouTube credentials are loaded from a JSON file.",
    "inputPattern": {
        "type": "object",
        "required": [
            "title",
            "upload",
            "category",
            "video_url",
            "description",
            "account_name"
        ],
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the video to be uploaded"
            },
            "upload": {
                "type": "boolean",
                "description": ""
            },
            "category": {
                "type": "string",
                "description": "Category of the video to be uploaded"
            },
            "video_url": {
                "type": "string",
                "description": "URL of the video to be uploaded to YouTube"
            },
            "description": {
                "type": "string",
                "description": "Description of the video to be uploaded"
            },
            "account_name": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "upload_success"
        ],
        "properties": {
            "upload_success": {
                "type": "boolean",
                "description": "A boolean flag indicating if the video was successfully uploaded to YouTube"
            }
        }
    },
    "tag": "UploadVideo",
    "testCases": [
        {
            "title": "Sample Video 1",
            "upload": false,
            "category": "Music",
            "video_url": "https://function-stable-diffusion.s3.ap-northeast-1.amazonaws.com/ai-video/output_1696843400_daefppdn.mp4",
            "description": "This is a sample video 1 for testing.",
            "account_name": "mindsflow.ai"
        },
        {
            "title": "Sample Video 2",
            "upload": false,
            "category": "Test",
            "video_url": "https://example.com/video2.mp4",
            "description": "This is a sample video 2 for testing.",
            "account_name": ""
        }
    ],
    "aiPrompt": "Upload video to youtube, input are video URL, title, description and category, delete the video after upload. Read youtube credentials from json file. Return succeeded True or False",
    "greeting": ""
}
$"""

from youtube_upload.client import YoutubeUploader
import json
import os
import requests

category_dict = {
    'Autos & Vehicles': '2',
     'Film & Animation': '1',
     'Music': '10',
     'Pets & Animals': '15',
     'Sports': '17',
     'Short Movies': '18',
     'Travel & Events': '19',
     'Gaming': '20',
     'Videoblogging': '21',
     'People & Blogs': '22',
     'Comedy': '23',
     'Entertainment': '24',
     'News & Politics': '25',
     'Howto & Style': '26',
     'Education': '27',
     'Science & Technology': '28',
     'Nonprofits & Activism': '29',
     'Movies': '30',
     'Anime/Animation': '31',
     'Action/Adventure': '32',
     'Classics': '33',
     'Documentary': '35',
     'Drama': '36',
     'Family': '37',
     'Foreign': '38',
     'Horror': '39',
     'Sci-Fi/Fantasy': '40',
     'Thriller': '41',
     'Shorts': '42',
     'Shows': '43',
     'Trailers': '44'
}

credentials_path = 'youtube'
config_file = f'{credentials_path}/api_tokens.json'

def download_file(url, new_file_name):
    response = requests.get(url)
    with open(new_file_name, 'wb') as f:
        f.write(response.content)
    return new_file_name

def mindsflow_function(event, context) -> dict:
    video_url = event.get("video_url")
    title = event.get("title")
    description = event.get("description")
    category = event.get("category")
    account_name = event.get("account_name")
    upload = event.get("upload", True)

    if upload == False:
        return {
            'upload_success': False
        }

    # download the video
    video_path = download_file(video_url, 'video_youtube.mp4')

    with open(config_file, 'r') as json_file:
        data = json.load(json_file)
    account = data[account_name]

    # Get the credentials
    refresh_token = account['refresh_token']
    access_token = account['access_token']
    secrets_file = account['secrets_file']

    uploader = YoutubeUploader(secrets_file_path=f'{credentials_path}/{secrets_file}')
    uploader.authenticate(refresh_token=refresh_token,
                        access_token=access_token)

    # Video options
    options = {
        "title" : title, # The video title
        "description" : description, # The video description
        "tags" : [],
        "categoryId" : category_dict[category],
        "privacyStatus" : "public", # Video privacy. Can either be "public", "private", or "unlisted"
        "kids" : True, # Specifies if the Video if for kids or not. Defaults to False.
        #"thumbnailLink" : "https://cdn.havecamerawilltravel.com/photographer/files/2020/01/youtube-logo-new-1068x510.jpg" # Optional. Specifies video thumbnail.
    }

    # upload video
    try:
        uploader.upload(video_path, options)
        success = True
    except:
        success = False

    os.remove(video_path)

    # define result
    result = {
        'upload_success': success
    }

    return result

        