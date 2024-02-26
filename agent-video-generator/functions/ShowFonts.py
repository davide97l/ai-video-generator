"""$
{
    "name": "ShowFonts",
    "displayName": "",
    "description": "Show fonts",
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
    "tag": "VideoCaptions",
    "testCases": [
        {}
    ],
    "aiPrompt": "",
    "greeting": ""
}
$"""

import json
from moviepy.editor import TextClip
import os
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import concatenate

FOLDER = 'fonts'    # specify the correct path

def mindsflow_function(event, context) -> dict:

    WIDTH, HEIGHT = 500, 500  # specify dimensions of each image
    BG_COLOR = (0, 0, 0)  # background color

    # Create images with each font
    images = []
    for file in os.listdir(FOLDER):
        if file.endswith(".ttf"):
            font = ImageFont.truetype(os.path.join(FOLDER, file), 50)
            image = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
            draw = ImageDraw.Draw(image)

            text = '{}'.format(file.replace('.ttf', ''))
            x = 10
            y = 150

            draw.text((x, y), text, fill=(255,255,255), font=font)
            images.append(image)

    # Calculate the grid size - 6 images per row
    rows = len(images) // 6
    if len(images) % 6:
        rows += 1

    # Concatenate all images into grid
    concat_image = Image.new('RGB', (WIDTH * 6, HEIGHT * rows), BG_COLOR)

    x_offset = 0
    y_offset = 0
    for i, img in enumerate(images):
        concat_image.paste(img, (x_offset, y_offset))
        if (i+1) % 6 == 0: 
            x_offset = 0 
            y_offset += HEIGHT 
        else: 
            x_offset += WIDTH 
    concat_image.save(f'{FOLDER}/fonts.jpg')

    result = {
        'fonts': f'{FOLDER}/fonts.jpg'
    }

    return result

        