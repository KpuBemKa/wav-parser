# import requests
# import base64
# from bs4 import BeautifulSoup
import pathlib
import time

from modules.audio_transcriber import AudioTranscriber
from modules.log import setup_custom_logger
from settings import LOGGER_NAME

logger = setup_custom_logger(LOGGER_NAME)


URL = "http://139.59.88.189:8069"

# File to upload
# file_path = "./home/esp-recordings/esp-recorder_2024-05-19_11-15-18.ogg"
# file_path = "./home/esp-recordings/vsauce_test_audio.mp3"
# file_path = "./home/esp-recordings/ru_input_wav.wav"
# file_path = "./home/esp-recordings/ru_input_wav_normalized.ogg"
file_path = "./home/esp-recordings/input1.ogg"

login_url = f"{URL}/web/login"
upload_url = f"{URL}/recs/new_rec"

AudioTranscriber().queue_audio_transcription(pathlib.PurePath(file_path))

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    exit()