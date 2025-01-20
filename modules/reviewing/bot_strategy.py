from pathlib import Path
from logging import getLogger
from abc import ABC, abstractmethod

import modules.bots.bot_replies as bot_replies

from .review_strategy import ReviewStrategy
from modules.models.issue import Issue
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
    def __init__(self, user_dialog: UserDialog) -> None:
        self.__user_dialog = user_dialog
        self.__audio_path: Path | None = None

    def handle_audio(self, audio_path: Path) -> None:
        self.__audio_path = audio_path
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is None:
            logger.warning("Transcription returned an empty value. Error?")
            self.__user_dialog.send_message(bot_replies.TRANSCRIPTION_ERROR)
            return

        self.handle_text(transcribed)

    def handle_text(self, text_message: str) -> None:
        review = ReviewAnalizer().summarize_review(text_message)
        
        if review is None:
            self.__user_dialog.send_message(bot_replies.TRANSCRIPTION_ERROR)
            return

        self.__user_dialog.send_message(self.__issues_to_text(review.issues))

        if not upload_review(
            audio_review_path=self.__audio_path,
            text_review=review.corrected_text,
            text_summary=review.summary,
            issues=review.issues,
        ):
            self.__user_dialog.send_message(bot_replies.UPLOAD_ERROR)

        # QR CODE SHOULD BE SENT HERE

    def __issues_to_text(self, issues: list[Issue]) -> str:
        if len(issues) == 0:
            return bot_replies.TRANSCRIPTION_DONE_NO_ISSUES

        issues_str_list = ""
        for issue in issues:
            issues_str_list += issue.description.strip(" \n") + "\n"

        return f"{bot_replies.TRANSCRIPTION_DONE_WITH_ISSUES}\n{issues_str_list}\n\n"
