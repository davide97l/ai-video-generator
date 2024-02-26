"""$
{
    "name": "returnInputParameters",
    "displayName": "",
    "description": "This method is designed to accept and return input parameters.",
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
    "tag": "ParameterReturn",
    "testCases": [
        {}
    ],
    "aiPrompt": "Return the input parameters",
    "greeting": ""
}
$"""

import json

def mindsflow_function(event, context) -> dict:
    # directly return the input parameters
    return event
        