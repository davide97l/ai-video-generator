import requests
import os
import json

data = {
    'character_name': 'elon_musk',
    'text': 'SpaceX aims to make humanity a multiplanetary species.'
}

response = requests.post('http://IP/generate_audio/', json=data)

with open('response.wav', 'wb') as f:
    f.write(response.content)

if response.status_code == 200:
    filename = 'result.wav'
    folder_name = 'results'
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    file_path = os.path.join(folder_name, filename)

    # Save the file to the directory
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f'File saved at {file_path}')
else:
    print('Failed to get response from the server.')