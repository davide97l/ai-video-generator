"""$
{
    "name": "translateTargetToSource",
    "displayName": "",
    "description": "This method is designed to translate text from one language to another, utilizing the target language as input and outputting the translation in the source language.",
    "inputPattern": {
        "type": "object",
        "required": [
            "text",
            "source_lang",
            "target_lang"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to be translated"
            },
            "source_lang": {
                "type": "string",
                "description": "Source language of the text"
            },
            "target_lang": {
                "type": "string",
                "description": "Target language to translate the text into"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [
            "text"
        ],
        "properties": {
            "text": {
                "type": "string",
                "description": "The translated text"
            }
        }
    },
    "tag": "Translation",
    "testCases": [
        {
            "text": "Hello world",
            "source_lang": "english",
            "target_lang": "chinese (simplified)"
        },
        {
            "text": "Guten tag",
            "source_lang": "",
            "target_lang": ""
        }
    ],
    "aiPrompt": "Translate a text from target language to source language",
    "greeting": ""
}
$"""

import json
from googletrans import Translator, LANGUAGES

def translate_text(text, source_language, target_language):
    #print(LANGUAGES.values())
    translator = Translator()

    if source_language not in LANGUAGES.values() or target_language not in LANGUAGES.values():
        return "Invalid source or target language."

    translation = translator.translate(text, src=source_language, dest=target_language)

    return translation.text

def mindsflow_function(event, context) -> dict:
    # get the text and languages from the event
    text = event.get("text")
    src_lang = event.get("source_lang")
    tgt_lang = event.get("target_lang")

    lang_dict = {
        'en': 'english',
        'zh': 'chinese (simplified)',
        'ch': 'chinese (simplified)',
        'de': 'german',
        'ge': 'german',
        'it': 'italian',
        'fr': 'french',
        'sp': 'spanish',
        'es': 'spanish',
    }
    if src_lang in lang_dict.keys():
        src_lang = lang_dict[src_lang]
    if tgt_lang in lang_dict.keys():
        tgt_lang = lang_dict[tgt_lang]

    # get the translation result
    translation_result = translate_text(text, src_lang, tgt_lang)

    # define result
    result = {
        'text': translation_result
    }

    return result

        