from pathlib import Path
from logging import getLogger

from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from modules.endpoints.upload_review import upload_review
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class DeviceStrategy(ReviewStrategy):
    def __init__(self) -> None:
        pass

    def handle_audio(self, audio_path: Path) -> None:
        self.__audio_path = audio_path
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is None:
            logger.warning("Transcription returned an empty value. Error?")
            return

        self.handle_text(transcribed)

    def handle_text(self, text_message: str) -> None:
        review = ReviewAnalizer().summarize_review(text_message)

        upload_review(
            audio_review_path=self.__audio_path,
            text_review=review.corrected_text,
            text_summary=review.summary,
            issues=review.issues,
        )
