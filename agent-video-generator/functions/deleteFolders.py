"""$
{
    "name": "deleteFolders",
    "displayName": "",
    "description": "delete all folders with exceptions",
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
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
import os
import glob
import shutil

exclude_list = [os.getenv('font_dir')]  # define your exclude list

def process_files(dir_path: str) -> list:
    # list all the subdirectories
    dir_paths = [d for d in glob.glob(os.path.join(dir_path, '*')) if os.path.isdir(d)]
    
    for dir_path in dir_paths:

        folder_name = os.path.basename(dir_path)
        # only delete the folder if it's not in the exclude list
        if folder_name not in exclude_list:

            # delete the folder
            shutil.rmtree(dir_path)
            print(f'Deleted: {dir_path}')

def mindsflow_function(event, context) -> dict:
    # get the directory path from the event
    dir_path = ''

    # process the directories and delete them
    process_files(dir_path)
    
    # define result
    result = {
        'status': 'ok'
    }

    return result

        