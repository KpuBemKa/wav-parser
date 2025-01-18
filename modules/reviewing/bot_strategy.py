from pathlib import Path
from logging import getLogger
from abc import ABC, abstractmethod

import modules.bots.bot_replies as bot_replies

from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from modules.endpoints.upload_review import upload_review
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class UserDialog(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        pass

    @abstractmethod
    def send_image(self, image_path: Path) -> None:
        pass


class BotReviewStrategy(ReviewStrategy):
    def __init__(self, bot_instance: UserDialog) -> None:
        self.__bot_instance = bot_instance

    def handle_audio(self, audio_path: Path) -> None:
        self.__audio_path = audio_path
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is None:
            logger.warning("Transcription returned an empty value. Error?")
            self.__bot_instance.send_message(bot_replies.TRANSCRIPTION_ERROR)
            return

        self.handle_text(transcribed)

    def handle_text(self, text_message: str) -> None:
        review = ReviewAnalizer().summarize_review(text_message)

        issues_str_list = ""
        for issue in review.issues:
            issues_str_list += issue.description + "\n"

        self.__bot_instance.send_message(f"{bot_replies.TRANSCRIPTION_DONE}\n{issues_str_list}\n\n")

        if not upload_review(
            audio_review_path=self.__audio_path,
            text_review=review.corrected_text,
            text_summary=review.summary,
            issues=review.issues,
        ):
            self.__bot_instance.send_message(bot_replies.UPLOAD_ERROR)

        # QR CODE SHOULD BE SENT HERE
