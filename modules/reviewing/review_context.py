# from time import sleep
# from logging import getLogger
# from pathlib import Path

# # from queue import SimpleQueue
# from threading import Thread

# from multiprocessing import Lock, Queue
# from .review_strategy import ReviewStrategy
# from modules.ais.audio_transcriber import AudioTranscriber
# from modules.ais.review_analizer import ReviewAnalizer
# from settings import LOGGER_NAME


# logger = getLogger(LOGGER_NAME)


# class ReviewPipeline:
#     def __init__(
#         self,
#         audio_queue: Queue[tuple[ReviewStrategy, Path]],
#         text_queue: Queue[tuple[ReviewStrategy, str]],
#         # audio_queue,
#         # text_queue,
#     ) -> None:
#         # if not self._initialized:
#         #     self._initialized = True

#         self.__audio_queue = audio_queue
#         self.__text_queue = text_queue
#         self.__lock = Lock()

#     def handle_audio(self, strategy: ReviewStrategy, audio_path: Path):
#         with self.__lock:
#             self.__audio_queue.put((strategy, audio_path))
#             logger.debug(f"Queued to transcribe audio file '{audio_path.as_posix()}'")

#     def handle_text(self, strategy: ReviewStrategy, text_review: str):
#         with self.__lock:
#             self.__text_queue.put((strategy, text_review))
#             logger.debug(f"Queued to analize text:\n{text_review}\n---")

#     def thread_executor(self) -> None:
#         # Setup AIs in specific order
#         AudioTranscriber()
#         ReviewAnalizer()

#         while True:
#             audio_available, text_available = False, False
#             with self.__lock:
#                 audio_available = not self.__audio_queue.empty()
#                 text_available = not self.__text_queue.empty()

#             if audio_available:
#                 with self.__lock:
#                     (strategy, audio_path) = self.__audio_queue.get()

#                 strategy.handle_audio(audio_path)

#             if text_available:
#                 with self.__lock:
#                     (strategy, text_review) = self.__text_queue.get()

#                 strategy.handle_text(text_review)

#             sleep(1)
