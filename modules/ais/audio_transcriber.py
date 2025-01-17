import subprocess
import time
import logging
import traceback
import pathlib
import torch

from transformers import pipeline

from modules.singleton_meta import SingletonMeta
from settings import DELETE_CONVERTED_FILES, LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


FAST_WHISPER_ARGS = {
    "language": "en",
    # "task": "translate",
    "max_new_tokens": 384,
}


class AudioTranscriber(metaclass=SingletonMeta):
    def __init__(self) -> None:
        # Setup the pipeline
        device = "cuda" if torch.cuda.is_available() else "cpu"
        device_int = 0 if device == "cuda" else -1
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        attn_impl = "spda"
        # model="openai/whisper-base",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details,
        model = "openai/whisper-large-v3-turbo"

        self.__pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            torch_dtype=torch_dtype,
            chunk_length_s=30,
            batch_size=1,
            return_timestamps=True,
            model_kwargs={"attn_implementation": attn_impl},
            device=device_int,
            generate_kwargs=FAST_WHISPER_ARGS,
        )

        logger.info(
            f"Running on {device} with id #{device_int}, using attn_implementation: {attn_impl}"
        )

    def transcribe_audio(self, audio_path: pathlib.Path) -> str | None:
        try:
            logger.info(f'Transcribing "{audio_path.as_posix()}" audio file...')

            # Normalize for speech
            audio_path = self.__try_normalize_for_speech(audio_path)

            # Convert to .ogg if it's not already
            if audio_path.suffix != ".ogg":
                logger.info("Audio file is not in .ogg format. Tying to convert it to .ogg...")
                audio_path = self.__try_convert_to_ogg(audio_path)

            # Transcribe audio file into text
            start_time = time.time()
            outputs = self.__pipe(audio_path.as_posix())
            end_time = time.time()

            transcribed_text = str(outputs["text"])

            logger.info(
                f"Audio '{audio_path.as_posix()}' transcribed in {end_time - start_time} seconds."
            )
            logger.info(f"Transcribed audio:\n{transcribed_text}")

            # Save transcribed text into a .txt file
            pathlib.Path(audio_path.with_suffix(".txt")).write_bytes(
                transcribed_text.encode("utf-8")
            )

            return transcribed_text

        except Exception as ex:
            logger.error(
                f"Exception catched durint audio transcription: {ex} {ex.args}\n{traceback.format_exc()}"
            )
            return None

    def __try_normalize_for_speech(self, input_audio: pathlib.Path) -> pathlib.Path:
        """
        Tries to normalize volume for speech in the given audio file.

        Returns the path to the converted file in case of success or
        the path to the original file in case of errors
        """

        logger.debug("Normalizing volume for speech...")

        # New file will have the same name
        output_path = input_audio

        # Original file will have a different name
        input_audio = input_audio.rename(
            input_audio.absolute().with_stem(f"{input_audio.stem}_original")
        )

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f"{input_audio.absolute().as_posix()}",
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
            return input_audio

        logger.info("Audio volume normalized for speech.")

        if DELETE_CONVERTED_FILES:
            # if the wav file was successfuly converted, no need to store it
            pathlib.Path(input_audio).unlink()

        return output_path

    def __try_convert_to_ogg(self, input_audio: pathlib.Path) -> pathlib.Path:
        """
        Tries to convert a .wav file to an .ogg one and normalize the volume.

        Returns the path to the converted file in case of success or
        the path to the original file in case of errors
        """
        logger.debug(f"Converting {input_audio} to .ogg...")

        # New file will have same name but different extension
        output_path = input_audio.with_suffix(".ogg")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f"{input_audio.absolute().as_posix()}",
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
            return input_audio

        logger.info("Audio file converted to .ogg")

        if DELETE_CONVERTED_FILES:
            # if the wav file was successfuly converted, no need to store it
            pathlib.Path(input_audio).unlink()

        return output_path

    # def __forward_data(
    #     self, file_name: str, file_path: pathlib.Path, transcription: str, summary: str
    # ):
    #     # Define the headers (use your access token for authorization)
    #     headers = {
    #         "API-Key": ODOO_API_KEY,
    #     }

    #     # Prepare the data payload
    #     data = {
    #         "file_name": file_name,
    #         "transcription": transcription,
    #         "summary": summary,
    #     }

    #     # Prepare the files payload
    #     files = {
    #         "file": open(file_path.as_posix(), "rb"),  # Open the file in binary mode
    #     }

    #     # Send the POST request
    #     response = requests.post(ODOO_UPLOAD_ENDPOINT, headers=headers, data=data, files=files)

    #     if response.status_code == 200:
    #         logger.info("File transcription has been successfuly uploaded to the remote enpoint")
    #     else:
    #         logger.error(
    #             f"File transcription upload has failed: {response.status_code} | Text:\n{response.text}"
    #         )
