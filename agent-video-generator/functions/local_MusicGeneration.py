"""$
{
    "name": "local_MusicGeneration",
    "displayName": "Local Music Generation",
    "description": "Generate music from prompt using local AudioCraft MusicGen instead of Replicate",
    "inputPattern": {
        "type": "object",
        "required": [
            "music_prompt"
        ],
        "properties": {
            "seed": {
                "type": "integer",
                "description": ""
            },
            "duration": {
                "type": "number",
                "description": ""
            },
            "temperature": {
                "type": "number",
                "description": ""
            },
            "music_prompt": {
                "type": "string",
                "description": ""
            },
            "model_size": {
                "type": "string",
                "description": "Model size: small, medium, large"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "music_url"
        ],
        "properties": {
            "music_url": {
                "type": "string",
                "description": ""
            }
        }
    },
    "tag": "VideoGeneration",
    "testCases": [
        {
            "seed": -1,
            "duration": 4.9,
            "temperature": 1,
            "music_prompt": "Create a classical music piece"
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

from local_music_gen import mindsflow_function as local_music_function

def mindsflow_function(event, context) -> dict:
    """
    Local implementation of MusicGeneration using AudioCraft MusicGen
    
    This is a drop-in replacement for the original Replicate MusicGen function.
    Uses local AudioCraft models for better quality and privacy.
    """
    # Pass through to the local implementation
    return local_music_function(event, context)