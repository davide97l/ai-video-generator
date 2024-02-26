"""$
{
    "name": "deleteFilesByExtension",
    "displayName": "",
    "description": "This method is used for deleting all files within a directory, with an optional filter for specific file extensions.",
    "inputPattern": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "status"
        ],
        "properties": {
            "status": {
                "type": "string",
                "description": "Indicates whether the operation was successful"
            }
        }
    },
    "tag": "FileDeletion",
    "testCases": [
        {},
        {}
    ],
    "aiPrompt": "delete all files in dir, can filter by extension",
    "greeting": ""
}
$"""

import json
import os
import glob

def process_files(dir_path: str, file_type: str) -> list:
    # construct the path with file type
    file_paths = glob.glob(os.path.join(dir_path, '*.' + file_type))


    # read and print file content
    for file_path in file_paths:
            print(file_path)
            os.remove(file_path)

def mindsflow_function(event, context) -> dict:
    # get the directory path and file type from the event
    dir_path = ''
    file_type = ['wav', 'mp4', 'json', 'html', 'log', 'zip', 'srt', 'mp3', 'jpg', 'ass']
    
    for ext in file_type:
        # process the files and get the content
        process_files(dir_path, ext)
    
    # define result
    result = {
        'status': 'ok'
    }

    return result

        