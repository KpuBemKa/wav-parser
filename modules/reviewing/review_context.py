from time import sleep
from logging import getLogger
from pathlib import Path, PurePath
# from multiprocessing import Queue
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
