from pathlib import Path
from time import sleep
from logging import getLogger
from uuid import uuid4 as generateUUID4, UUID
from multiprocessing import Lock, Queue

# from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from modules.models.review_result import ReviewResult

from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class ReviewPipeline:
    def __init__(
        self,
        # audio_queue: Queue[tuple[UUID, Path]],
        # text_queue: Queue[tuple[UUID, str]],
        # result_queue: list[tuple[UUID, ReviewResult]],
        audio_queue,
        text_queue,
        results_dict,
    ) -> None:
        self.__audio_queue: Queue[tuple[UUID, Path]] = audio_queue
        self.__text_queue: Queue[tuple[UUID, str]] = text_queue
        self.__result_list: dict[UUID, ReviewResult] = results_dict
        self.__results_lock = Lock()

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

    def get_result_by_uuid(self, uuid: UUID) -> ReviewResult | None:
        with self.__results_lock:
            if uuid in self.__result_list:
                return self.__result_list.pop(uuid)
            # for _uuid in self.__result_list:
            #     if _uuid == uuid:
            #         return _result

    def thread_executor(self) -> None:
        AudioTranscriber()
        ReviewAnalizer()

        while True:
            if not self.__audio_queue.empty():
                (uuid, audio_path) = self.__audio_queue.get()
                result = self.__handle_audio(audio_path)

                with self.__results_lock:
                    self.__result_list[uuid] = result

            if not self.__text_queue.empty():
                (uuid, text_review) = self.__text_queue.get()
                result = self.__handle_text(text_review)

                with self.__results_lock:
                    self.__result_list[uuid] = result

            sleep(1)

    def __handle_audio(self, audio_path: Path) -> ReviewResult:
        transcribed = AudioTranscriber().transcribe_audio(audio_path)

        if transcribed is None:
            logger.error("Transcription returned an empty value. Error?")
            return ReviewResult(completed=False)

        return self.__handle_text(transcribed)

    def __handle_text(self, text_message: str) -> ReviewResult:
        review = ReviewAnalizer().summarize_review(text_message)

        if review is None:
            logger.error("Analyzer returned an empty value. Error?")
            return ReviewResult(completed=False)

        return review
