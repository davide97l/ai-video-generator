"""$
{
    "name": "MindsflowAgent",
    "displayName": "",
    "description": "Example of how to invoke Mindsflow agent",
    "inputPattern": {
        "type": "object",
        "required": [
            "input_str"
        ],
        "properties": {
            "input_str": {
                "type": "string",
                "description": "The input string to be translated"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "translated_text"
        ],
        "properties": {
            "translated_text": {
                "type": "string",
                "description": "translation result"
            }
        }
    },
    "tag": "Example",
    "testCases": [
        {
            "input_str": "hello"
        }
    ],
    "aiPrompt": "aa",
    "greeting": ""
}
$"""

import json

def translate_text(input_str: str, event) -> str:
    data = {
        "style": "LLM-Only",
        "stream": False,
        "messageContent": input_str,
        "agentId": 739
    }

    resp = event.chat.messages(data=data)

    return resp

def mindsflow_function(event, context) -> dict:
    # get the input string from the event
    input_str = event.get("input_str")
    
    # get the translation result
    translated_text = translate_text(input_str, event)
    
    # define result
    result = {
        'translated_text': translated_text
    }

    return result

        