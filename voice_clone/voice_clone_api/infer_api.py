from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from fastapi.responses import FileResponse
import argparse
import logging
import uvicorn
from infer import *

app = FastAPI()
dataset_raw = 'dataset_raw'
logs = 'logs'
config = "config_1000"


@app.post("/generate_voice")
async def generate_audio_file(data: dict):
    print('Received audio generation request data: ', data)
    dataset = data['voice']
    audio_url = data['audio_url']
    clean_noise = data['clean_noise']

    try:
        generated_audio = infer(audio_url, dataset, config, clean_noise=clean_noise)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

    response = FileResponse(generated_audio, filename=generated_audio)
    return response


# python3 infer_api.py --port 5000
if __name__ == "__main__":
    # Setting up argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run server on, default is 8000.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=args.port)
