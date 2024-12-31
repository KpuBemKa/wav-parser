import subprocess
import threading
import time
import logging
import traceback
import requests
import pathlib
import torch

from queue import SimpleQueue, Empty
from transformers import pipeline
from threading import Lock

from modules.singleton_meta import SingletonMeta
from settings import DELETE_CONVERTED_FILES, ODOO_UPLOAD_ENDPOINT, LOGGER_NAME
from keys import ODOO_API_KEY


logger = logging.getLogger(LOGGER_NAME)


class AudioTranscriber(metaclass=SingletonMeta):
    def __init__(self) -> None:
        # model="openai/whisper-base",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
        # torch_dtype=torch.float32,
        # device="cuda:0",  # or mps for Mac devices
        # model_kwargs={"attn_implementation": "flash_attention_2"} if is_flash_attn_2_available() else {"attn_implementation": "sdpa"},
        # model_kwargs={"attn_implementation": "sdpa"},

        self.__queue = SimpleQueue()
        self.__thread: threading.Thread | None = None

        # threading.Thread(target=self.__main_thread, daemon=True).start()

    def queue_audio_transcription(self, audio_file_path: pathlib.PurePath) -> None:
        if self.__thread is None:
            self.__thread = threading.Thread(target=self.__main_thread, daemon=True).start()
        
        self.__queue.put(pathlib.Path(audio_file_path))

    def __main_thread(self) -> None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        device_int = 0 if device == "cuda" else -1
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        # attn_impl = "flash_attention_2" if is_flash_attn_2_available() else "spda"
        attn_impl = "spda"

        self.__pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-base",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details,
            # tokenizer=processor.tokenizer,
            # feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            torch_dtype=torch_dtype,
            chunk_length_s=30,
            batch_size=24,
            return_timestamps=True,
            model_kwargs={"attn_implementation": "sdpa"},
            device=device_int,
        )
        
        logger.info(f"Running on {device}, with attn_implementation: {attn_impl}")

        while True:
            if self.__queue.empty():
                time.sleep(1)
                continue

            try:
                self.__transcribe_audio(self.__queue.get(timeout=10))
            except Empty:
                continue

    def __transcribe_audio(self, audio_path: pathlib.Path) -> None:
        try:
            # Transcribe audio file into text
            logger.info(f'Transcribing "{audio_path.as_posix()}" audio file...')

            if audio_path.suffix == ".wav":
                print("Normalizing volume for speech...")
                audio_path = self.__try_normalize_for_speech(audio_path)

            start_time = time.time()
            outputs = self.__pipe(
                audio_path.as_posix(),
                chunk_length_s=30,
                batch_size=24,
                return_timestamps=False,
            )
            end_time = time.time()

            logger.info(
                f"Audio '{audio_path.as_posix()}' transcribed in {end_time - start_time} seconds."
            )
            logger.info(f"Transcribed audio: {outputs['text']}")

            # If input file is a .wav, try to convert it to an .ogg,
            # because telegram's `sendVoice` command accepts only .mp3, .ogg & .m4a,
            # and also because a spectogram of a voice recording can be made only from
            # an .ogg file encoded with Opus
            if audio_path.suffix == ".wav":
                logger.info("Audio file is in .wav format. Tying to converting it to .ogg...")
                audio_path = self.__try_convert_wav_to_ogg(audio_path)

            # Save transcribed text into a .txt file
            pathlib.Path(audio_path.with_suffix(".txt")).write_bytes(
                str(outputs["text"]).encode("utf-8")
            )

            self.__forward_data(
                file_name=audio_path.name,
                file_path=audio_path,
                transcription=str(outputs["text"]),
            )

        except Exception as ex:
            print(f"Exception catched: {ex} {ex.args}\n{traceback.format_exc()}")

    def __try_normalize_for_speech(self, wav_path: pathlib.Path) -> pathlib.Path:
        """
        Tries to normalize volume for speech in the given .wav file.

        Returns the path to the converted file in case of success or
        the path to the original file in case of errors
        """

        output_path = wav_path.with_stem(f"{wav_path.stem}_normalized")

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f"{wav_path.absolute().as_posix()}",
                    "-af",
                    "volume=1.7, arnndn=m=mp.rnnn",
                    "-acodec",
                    "pcm_s16le",
                    "-f",
                    "wav",
                    f"{output_path.absolute().as_posix()}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as ex:
            logger.error(f"Command failed with exit code: {ex.returncode}:\n{ex.stderr}")
            return wav_path

        logger.info("Audio volume normalized for speech.")

        if DELETE_CONVERTED_FILES:
            # if the wav file was successfuly converted, no need to store it
            pathlib.Path(wav_path).unlink()

        return output_path

    def __try_convert_wav_to_ogg(self, wav_path: pathlib.Path) -> pathlib.Path:
        """
        Tries to convert a .wav file to an .ogg one and normalize the volume.

        Returns the path to the converted file in case of success or
        the path to the original file in case of errors
        """
        output_path = wav_path.with_stem(f"{wav_path.stem}_normalized")

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f"{wav_path.absolute().as_posix()}",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "64k",
                    f"{output_path.absolute().as_posix()}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as ex:
            logger.error(f"Command failed with exit code: {ex.returncode}:\n{ex.stderr}")
            return wav_path

        logger.info("Audio file converted to .ogg")

        if DELETE_CONVERTED_FILES:
            # if the wav file was successfuly converted, no need to store it
            pathlib.Path(wav_path).unlink()

        return output_path

    def __forward_data(self, file_name: str, file_path: pathlib.Path, transcription: str):
        # Define the headers (use your access token for authorization)
        headers = {
            "API-Key": ODOO_API_KEY,
        }

        # Prepare the data payload
        data = {
            "file_name": file_name,
            "transcription": transcription,
        }

        # Prepare the files payload
        files = {
            "file": open(file_path.as_posix(), "rb"),  # Open the file in binary mode
        }

        # Send the POST request
        response = requests.post(ODOO_UPLOAD_ENDPOINT, headers=headers, data=data, files=files)

        if response.status_code == 200:
            logger.info("File transcription has been successfuly uploaded to the remote enpoint")
        else:
            logger.error(
                f"File transcription upload has failed: {response.status_code} | Text:\n{response.text}"
            )
