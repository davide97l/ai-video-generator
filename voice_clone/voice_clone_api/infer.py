from functions import *


audio_path = '../results'
dataset_raw = 'dataset_raw'
logs = 'logs'

# reference: https://github.com/svc-develop-team/so-vits-svc


def infer(audio_url, dataset_name, config, clean_noise=False):
    os.system(f"wget {audio_url}")
    audio_name = audio_url.split('/')[-1].split('.')[0]
    audio_name_with_ext = audio_url.split('/')[-1]
    ext = audio_name_with_ext.split('.')[-1]
    if ext == 'mp3':
        audio_name_with_ext = convert_mp3_to_wav(audio_name_with_ext)
    if not os.path.exists(f"{audio_path}"):
        os.system(f"mkdir {audio_path}")
    if clean_noise:
        audio_name_with_ext = reduce_noise(audio_name_with_ext)
    os.system(f"mv {audio_name_with_ext} {audio_path}")
    os.system(f"svc infer {audio_path}/{audio_name_with_ext} -m {logs}/{dataset_name}/ -c {logs}/{config}.json")
    os.system(f"rm {audio_path}/{audio_name_with_ext}")
    #os.system(f"mv {audio_name}.out.wav {audio_path}")
    return f"{audio_path}/{audio_name}.out.wav"
