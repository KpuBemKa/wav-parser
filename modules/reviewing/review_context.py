from time import sleep
from logging import getLogger
from pathlib import Path
from queue import SimpleQueue
from threading import Thread

from .review_strategy import ReviewStrategy
from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer
from modules.singleton_meta import SingletonMeta
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)


class ReviewContext(metaclass=SingletonMeta):
    def __init__(self) -> None:
        # self.__strategy = strategy
        self.__audio_queue: SimpleQueue[tuple[ReviewStrategy, Path]] = SimpleQueue()
        self.__text_queue: SimpleQueue[tuple[ReviewStrategy, str]] = SimpleQueue()
        self.__thread: Thread | None = None

    def handle_audio(self, strategy: ReviewStrategy, audio_path: Path):
        if self.__thread is None:
            logger.info("Thread is None")
            self.__start_thread()

        self.__audio_queue.put((strategy, audio_path))
        logger.debug(f"Queued to transcribe audio file '{audio_path.as_posix()}'")

    def handle_text(self, strategy: ReviewStrategy, text_review: str):
        if self.__thread is None:
            logger.info("Thread is None")
            self.__start_thread()

        self.__text_queue.put((strategy, text_review))
        logger.debug(f"Queued to analize text:\n{text_review}\n---")

    def __start_thread(self):
        self.__thread = Thread(target=self.__thread_executor, daemon=True)
        self.__thread.start()

    def __thread_executor(self) -> None:
        # Setup AIs in specific order
        AudioTranscriber()
        ReviewAnalizer()

        while True:
            if not self.__audio_queue.empty():
                (strategy, audio_path) = self.__audio_queue.get(block=True, timeout=10)
                strategy.handle_audio(audio_path)

            if not self.__text_queue.empty():
                (strategy, text_review) = self.__text_queue.get(block=True, timeout=10)
                strategy.handle_text(text_review)

            sleep(1)
