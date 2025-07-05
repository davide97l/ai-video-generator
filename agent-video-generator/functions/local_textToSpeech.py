"""$
{
    "name": "local_textToSpeech",
    "displayName": "Local Text-to-Speech",
    "description": "Convert text to speech using local Coqui XTTS v2 instead of Azure TTS",
    "inputPattern": {
        "type": "object",
        "required": [
            "text"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert into voice"
            },
            "speaker": {
                "type": "string",
                "description": "speaker"
            },
            "language": {
                "type": "string",
                "description": "Voice language"
            },
            "voice_speed": {
                "type": "number",
                "description": "voice speed"
            },
            "speaker_wav": {
                "type": "string",
                "description": "Path to reference speaker audio for voice cloning"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "duration",
            "audio_url"
        ],
        "properties": {
            "duration": {
                "type": "number",
                "description": ""
            },
            "audio_url": {
                "type": "string",
                "description": "URL address of the generated voice"
            }
        }
    },
    "tag": "TextToSpeech",
    "testCases": [
        {
            "text": "Hi, my name is Hello world",
            "speaker": "en-US-GuyNeural",
            "language": "en",
            "voice_speed": 1
        },
        {
            "text": "What is the weather today?",
            "speaker": "",
            "language": "en",
            "voice_speed": 1
        },
        {
            "text": "Mi piace mangiare la pasta",
            "speaker": "",
            "language": "it",
            "voice_speed": 1
        }
    ],
    "aiPrompt": "The method converts a given text string into audio using local XTTS v2 model with voice cloning capability",
    "greeting": ""
}
$"""

import sys
import os

# Add the local_ai directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'local_ai'))

from local_tts import mindsflow_function as local_tts_function

def mindsflow_function(event, context) -> dict:
    """
    Local implementation of textToSpeech using Coqui XTTS v2
    
    This is a drop-in replacement for the original Azure TTS function.
    Supports voice cloning and multiple languages with better quality.
    """
    # Pass through to the local implementation
    return local_tts_function(event, context)