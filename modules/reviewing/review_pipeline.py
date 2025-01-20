from pathlib import Path
from collections.abc import Callable
from multiprocessing import Lock, Queue
from time import sleep
from logging import getLogger
from uuid import uuid4 as generateUUID4, UUID

# from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from modules.models.review_result import ReviewResult, Issue
from modules.models.issue_department import IssueDepartment
from modules.endpoints.upload_review import upload_review

from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)
DONE_CALLBACK_TYPE = Callable[[ReviewResult | None], None]


class ReviewPipeline:
    def __init__(
        self,
        # audio_queue: Queue[tuple[UUID, Path]],
        # text_queue: Queue[tuple[UUID, str]],
        # result_queue: list[tuple[UUID, ReviewResult | None]],
        audio_queue,
        text_queue,
        result_queue,
    ) -> None:
        self.__audio_queue = audio_queue
        self.__text_queue = text_queue
        self.__result_list = result_queue

    def queue_audio(self, audio_path: Path) -> UUID:
        work_uuid = generateUUID4()

        self.__audio_queue.put((work_uuid, audio_path))

        logger.debug(f"Queued to transcribe audio file '{audio_path.as_posix()}'")
        return work_uuid

    def queue_text(self, text_review: str) -> UUID:
        work_uuid = generateUUID4()

        self.__text_queue.put((work_uuid, text_review))

        logger.debug(f"Queued to analize text:\n{text_review}\n---")
        return work_uuid

    def get_result_list(self):
        return self.__result_list

    def thread_executor(self) -> None:
        AudioTranscriber()
        ReviewAnalizer()

        while True:
            audio_available = not self.__audio_queue.empty()
            text_available = not self.__text_queue.empty()

            if audio_available:
                (uuid, audio_path) = self.__audio_queue.get()
                self.__result_list.append((uuid, self.__handle_audio(audio_path)))

            if text_available:
                (uuid, text_review) = self.__text_queue.get()
                self.__result_list.append((uuid, self.__handle_text(text_review)))

            sleep(1)

    def __handle_audio(self, audio_path: Path) -> ReviewResult | None:
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is None:
            logger.warning("Transcription returned an empty value. Error?")
            return

        self.__handle_text(transcribed, audio_path)

    def __handle_text(
        self, text_message: str, audio_path: Path | None = None
    ) -> ReviewResult | None:
        # return ReviewResult("a", "b", [Issue("c", IssueDepartment.BAR)])

        review = ReviewAnalizer().summarize_review(text_message)

        if review is None:
            logger.warning("Analyzer returned an empty value. Error?")
            return

        if upload_review(
            audio_review_path=audio_path,
            text_review=review.corrected_text,
            text_summary=review.summary,
            issues=review.issues,
        ):
            return review

        # QR CODE SHOULD BE SENT HERE
