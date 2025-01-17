import pathlib

from collections.abc import Callable

from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer


class BotStrategy:
    def __init__(self, send_message_func: Callable[[str], None]) -> None:
        self.__send_message_func = send_message_func

    def handle_audio(self, audio_path: pathlib.Path) -> None:
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is not None:
            review = ReviewAnalizer().summarize_review(transcribed)
            print(review.corrected_text)
            print(review.summary)
            print(review.issues.__dict__)
