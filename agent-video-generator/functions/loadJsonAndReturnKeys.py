"""$
{
    "name": "loadJsonAndReturnKeys",
    "displayName": "",
    "description": "This method takes a string input, interprets it as a JSON object, and returns each key within it as a string.",
    "inputPattern": {
        "type": "object",
        "required": [
            "json_string"
        ],
        "properties": {
            "json_string": {
                "type": "string",
                "description": "A JSON string variable"
            }
        }
    },
    "outputPattern": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "tag": "DataPreprocessing",
    "testCases": [
        {
            "json_string": "{\n\\\"Title\\\": \\\"The Enchantments of the Mystic World\\\",\n\\\"Text\\\": \\\"In a land of dreams and lore, where mythical beasts roar under an eternally twilight sky, unfurls the enigma of a fantasy style poem. Weaving an intricate tapestry of knights and elves, wizards and dragons, this poem is a saga of heroic adventures and epic battles. Dreamlike imagery is brushstroked with sonorous verses, blending the borders of reality with the enchanting realm of magical dimensions.\\\",\n\\\"Description\\\": \\\"A brief depiction of a fantasy style poem enriching the mystical world of myths and magic, injecting life into fictional characters and their bewitching land.\\\",\n\\\"Prompt\\\": \\\"An epic painting of mythical creatures like dragons and unicorns embarking on heroic adventures, with knights and elves in a magical realm under a twilight sky.\\\",\n\\\"Hashtags\\\": \\\"#SpartanRace #SpearThrow #ObstacleCourse #FitnessGoals #RaceTraining #Endurance #GetSpartanFit\\\"\\n\n}"
        }
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json

def json_from_string(json_str: str) -> dict:
    return json.loads(json_str)

def mindsflow_function(event, context) -> dict:
    json_string = event.get("json_string").replace('\\n', '').replace('\n', '').replace('\\', '')
    print(json_string)
    json_data = json.loads(json_string)

    keys = ', '.join([str(elem) for elem in json_data.keys()])

    results = {}

    for k in json_data.keys():
        results[k.lower()] = json_data[k]
        if k.lower() == 'description' and 'Hashtags' in json_data.keys():
            results[k.lower()] += '\n' + json_data['Hashtags'].lower()
    
    return results

        