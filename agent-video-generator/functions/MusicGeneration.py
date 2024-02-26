"""$
{
    "name": "MusicGeneration",
    "displayName": "",
    "description": "Generate music from prompt",
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

import json
from os import path
import math

'''import subprocess
command = 'pip install replicate'
process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)'''
import replicate


# Function to create a short music
def create_music(prompt: str, duration: int=15, temperature: float=1, seed: int=-1) -> str:
    output = replicate.run(
        "meta/musicgen:7be0f12c54a8d033a0fbd14418c9af98962da9a86f5ff7811f9b3423a1f0b7d7",
        input={"model_version": "large",
               "prompt": prompt,
               "duration": duration,
               "temperature": temperature,
               "seed": seed}
    )

    return output

def mindsflow_function(event, context) -> dict:
    # get the prompt from the event
    prompt = event.get("music_prompt")
    duration = event.get("duration", 15)
    duration = min(duration, 28)
    temperature = event.get("temperature", 1)
    seed = event.get("seed", -1)
    if isinstance(duration, float):
        duration = math.ceil(duration)  # Convert to int and approximate by excess

    # get the music URL
    music_url = create_music(prompt, duration, temperature, seed)

    # define result
    result = {
        'music_url': music_url
    }

    return result

        