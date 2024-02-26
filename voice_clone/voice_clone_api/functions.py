from pydub import AudioSegment
import os
from scipy.io import wavfile
import noisereduce as nr
import numpy as np
import wave
import requests


def is_stereo(filename):
    with wave.open(filename, 'rb') as wav_file:
        channels = wav_file.getnchannels()

    if channels == 2:
        return True
    else:
        return False


def reduce_noise(file_name):
    if file_name.split('.')[-1] != 'wav':
        file_name = convert_mp3_to_wav(file_name, remove_original=True)
    rate, data = wavfile.read(file_name)
    if is_stereo(file_name):
        # from https://github.com/timsainb/noisereduce/issues/57
        data1 = data[:,0]
        data2 = data[0:,1]
        # perform noise reduction
        reduced_noise1 = nr.reduce_noise(y=data1, sr=rate)
        reduced_noise2 = nr.reduce_noise(y=data2, sr=rate)
        reduced_noise = np.stack((reduced_noise1, reduced_noise2), axis=1)
    else:
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
    wavfile.write(file_name, rate, reduced_noise)
    return file_name


def split_audio(input_file, duration):
    # Load audio file
    audio = AudioSegment.from_file(input_file)

    # Length of audio file
    length_audio = len(audio)

    # Split audio file into chunks of 'duration'
    chunks = [audio[i:i+duration*1000] for i in range(0, length_audio, duration*1000)]

    # Save chunks in the same folder as the original file
    for i, chunk in enumerate(chunks):
        chunk_name = f'{input_file[:-4]}_chunk_{i}.wav'
        print(f'Created {chunk_name}')
        chunk.export(chunk_name, format='wav')


def convert_mp3_to_wav(file_path, remove_original=True):
    audio = AudioSegment.from_mp3(file_path)
    output_path = change_file_extension(file_path, 'wav')
    audio.export(output_path, format="wav")
    if remove_original:
        os.remove(file_path)
    return output_path


def change_file_extension(filename, new_extension):
    # Get the file name without the old extension
    base = os.path.splitext(filename)[0]
    # Return the file name with the new extension
    return base + '.' + new_extension


def download_file(url, filename):
    r = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(r.content)
