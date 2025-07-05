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
current_dir = os.path.dirname(os.path.abspath(__file__))
local_ai_dir = os.path.join(current_dir, '..', '..', 'local_ai')
sys.path.insert(0, local_ai_dir)

try:
    from local_music_gen import mindsflow_function as local_music_function
except ImportError as e:
    print(f"Error importing local_music_gen: {e}")
    print("Make sure to run 'python setup_local_ai.py' first")
    raise

def mindsflow_function(event, context) -> dict:
    """
    Local implementation of MusicGeneration using AudioCraft MusicGen
    
    This is a drop-in replacement for the original Replicate MusicGen function.
    Uses local AudioCraft models for better quality and privacy.
    """
    # Pass through to the local implementation
    return local_music_function(event, context)