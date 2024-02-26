from fastapi import FastAPI, UploadFile, File, HTTPException
import logging
import uvicorn
from train import *

app = FastAPI()
dataset_raw = 'dataset_raw'
logs = 'logs'


@app.post("/voice_clone")
async def generate_audio_file(data: dict):
    print('Received audio generation request data: ', data)
    dataset = data['dataset_url']
    split = data['split']
    config = data['config']
    clean_noise = data['clean_noise']
    try:
        dataset_name = preprocess(dataset, split_threshold=split, clean_noise=clean_noise)
        train(dataset_name, config)
        clean()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

    return {
        "succeeded": True,
        "voice": dataset_name,
    }


# python3 train_api.py --port 5000
if __name__ == "__main__":
    # Setting up argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run server on, default is 8000.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=args.port)
