"""$
{
    "name": "CommandsExecution",
    "displayName": "",
    "description": "CommandsExecution",
    "inputPattern": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "outputPattern": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "tag": "Example",
    "testCases": [
        {}
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json

def mindsflow_function(event, context) -> dict:
    """
    This is the main function that processes an event within a given context.

    Args:
        event (class Event): Containing mindsflow internal api and request information.
            case1: event.get("param")  # inference parameters
            case2: event.chat.messages(data)  # call mindsflow api
        context (class Context): Containing execution context and additional environment information.

    Returns:
        dict: A result dictionary meeting the Output Pattern.
    """
    import zipfile
    import subprocess

    '''def unzip_folder(path_to_zip_file, directory_to_extract_to):
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)'''

    # usage
    #unzip_folder("fonts.zip", "fonts")

    def execute_command(command):
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    execute_command("pip uninstall spleeter")

    result = {
        'data': 'Hello, MindsFlow User!'
    }

    return result

        