"""$
{
    "name": "local_generateVideoScript",
    "displayName": "Local Video Script Generator",
    "description": "Generate video script using local Llama model instead of external APIs",
    "inputPattern": {
        "type": "object",
        "required": [
            "topic"
        ],
        "properties": {
            "topic": {
                "type": "string",
                "description": ""
            },
            "text_style": {
                "type": "string",
                "description": ""
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "json_string"
        ],
        "properties": {
            "json_string": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "VideoGeneration",
    "testCases": [
        {
            "topic": "Benefits of eating mango",
            "text_style": "scientific, straight to the point, easy to read"
        },
        {
            "topic": "Story of two brothers, sci-fi",
            "text_style": ""
        },
        {
            "topic": "story, sci-fi, epic",
            "text_style": ""
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import sys
import os

# Add the local_ai directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'local_ai'))

from local_llm import mindsflow_function as local_script_function

def mindsflow_function(event, context) -> dict:
    """
    Local implementation of generateVideoScript using local LLM
    
    This is a drop-in replacement for the original function that uses
    local Llama model instead of external Mindsflow agents.
    """
    # Simply pass through to the local implementation
    return local_script_function(event, context)