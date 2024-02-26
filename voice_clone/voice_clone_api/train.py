import os
from pydub import AudioSegment
from functions import split_audio, reduce_noise, download_file
import argparse


dataset_raw = 'dataset_raw'
logs = 'logs'

# reference: https://github.com/svc-develop-team/so-vits-svc


def preprocess(dataset_path: str, split_threshold: int = 12, f0_method='dio', clean_noise=False):
    # dataset zip url
    if not os.path.exists(dataset_raw):
        os.mkdir(dataset_raw)
    os.system(f"wget {dataset_path}")
    dataset_name = dataset_path.split('/')[-1].split('.')[0]
    print('Dataset name:', dataset_name)
    dataset_dir = os.path.join(dataset_raw, dataset_name)
    if not os.path.exists(dataset_dir):
        os.mkdir(dataset_dir)
    print('Created dir:',  dataset_dir)
    os.system(f"mv {dataset_name}.zip {dataset_raw}")
    os.system(f"unzip {dataset_raw}/{dataset_name}.zip -d {dataset_raw}")
    # after unzip, if the file contains a single file, create folder in {dataset_raw} with the name of the file and
    # move the wav file to that folder
    files = [f for f in os.listdir(dataset_raw) if f.endswith('.wav')]
    if len(files) == 1:
        single_file = files[0]
        file_name, file_ext = os.path.splitext(single_file)
        new_folder_path = f"{dataset_raw}/{file_name}"
        os.system(f"mkdir {new_folder_path}")
        os.system(f"mv {dataset_raw}/{single_file} {new_folder_path}")

    os.system(f"rm {dataset_raw}/{dataset_name}.zip")

    if os.path.exists(os.path.join(dataset_raw, '__MACOSX')):
        os.system(f"rm -rf {dataset_raw}/__MACOSX")
    if os.path.exists(os.path.join('dataset/44k', '__MACOSX')):
        os.system(f"rm -rf dataset/44k/__MACOSX")

    for root,  _, files in os.walk(dataset_dir):
        for name in files:
            filename = os.path.join(root, name)
            if filename.endswith((".mp3", ".wav")):

                if clean_noise:
                    filename = reduce_noise(filename)

                # Split long audio file into smaller chunks
                audio = AudioSegment.from_file(filename)
                duration_seconds = len(audio) / 1000  # duration in seconds
                if duration_seconds > split_threshold:
                    split_audio(filename, split_threshold)
                    os.remove(filename)
                    print(f'Removed {filename}')

    os.system("svc pre-resample")
    os.system("svc pre-config")
    os.system(f"svc pre-hubert -fm {f0_method}")
    return dataset_name


def train(dataset_name, config):
    if not os.path.exists(logs):
        os.mkdir(logs)
    if 'http' in config:
        download_file(config, f"{logs}/custom_config.json")
        config = f"{logs}/custom_config.json"
    else:
        if '.json' in config:
            config = config.split('.json')[0]
        config = f'{logs}/{config}.json'
    if os.path.exists(f"{logs}/{dataset_name}"):
        os.system(f"rm -rf {logs}/{dataset_name}")
    if not os.path.exists(f"{logs}/{dataset_name}"):
        os.mkdir(f"{logs}/{dataset_name}")
    os.system(f"svc train --model-path {logs}/{dataset_name} --config-path {config}")
    # svc train --model-path logs/davide_en --config-path logs/config_100.json


def clean():
    os.system(f"rm -rf {dataset_raw}")
    os.system(f"rm -rf dataset")
    os.system(f"rm -rf filelists")

