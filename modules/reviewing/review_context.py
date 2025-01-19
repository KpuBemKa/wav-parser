from time import sleep
from logging import getLogger
from pathlib import Path, PurePath
from queue import Queue
from threading import Thread

from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class ReviewQueues:
    audio_queue: Queue[tuple[ReviewStrategy, Path]] = Queue()
    text_queue: Queue[tuple[ReviewStrategy, str]] = Queue()


class ReviewContext:
    def __init__(self, review_queues: ReviewQueues) -> None:
        self.__queues = review_queues
        # self.__thread: Thread | None = None
        # self.__thread = Thread(target=self.__thread_executor, daemon=True)
        # self.__thread.start()

    # def handle_audio(self, strategy: ReviewStrategy, audio_path: Path):
    #     if self.__thread is None:
    #         logger.info("Thread is None")
    #         self.__start_thread()

    #     self.__queues.audio_queue.put((strategy, audio_path))
    #     logger.debug(f"Queued to transcribe audio file '{audio_path.as_posix()}'")

    # def handle_text(self, strategy: ReviewStrategy, text_review: str):
    #     if self.__thread is None:
    #         logger.info("Thread is None")
    #         self.__start_thread()

    #     self.__text_queue.put((strategy, text_review))
    #     logger.debug(f"Queued to analize text:\n{text_review}\n---")

    # def start_thread(self):
    #     self.__thread = Thread(target=self.__thread_executor, daemon=True)
    #     self.__thread.start()

    def run_reviewing(self) -> None:
        # Setup AIs in specific order
        AudioTranscriber()
        ReviewAnalizer()

        while True:
            if not self.__queues.audio_queue.empty():
                (strategy, audio_path) = self.__queues.audio_queue.get(block=True, timeout=10)
                strategy.handle_audio(Path(audio_path))

            if not self.__queues.text_queue.empty():
                (strategy, text_review) = self.__queues.text_queue.get(block=True, timeout=10)
                strategy.handle_text(text_review)

            sleep(1)
