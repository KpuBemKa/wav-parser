from multiprocessing.managers import BaseManager
from multiprocessing import Process, Manager, Queue
from threading import Thread

from modules.bots.tg_bot import start_tg_bot
from modules.ftp_server import start_ftp_server
from modules.review_pipeline import ReviewPipeline
from modules.log import setup_custom_logger
from settings import LOGGER_NAME


"""
TODO
- timeout for wait for result
"""


logger = setup_custom_logger(LOGGER_NAME)


class ContextManager(BaseManager):
    pass


if __name__ == "__main__":
    ContextManager.register("ReviewPipeline", ReviewPipeline)

    with ContextManager() as manager:
        audio_queue = Manager().Queue()
        text_queue = Manager().Queue()
        results_dict = Manager().dict()
        shared_review_context: ReviewPipeline = manager.ReviewPipeline(
            audio_queue, text_queue, results_dict
        )

        review_context_thread = Thread(target=shared_review_context.thread_executor, name="Review")
        ftp_process = Process(target=start_ftp_server, args=(shared_review_context,), name="FTP")
        tg_process = Process(target=start_tg_bot, args=(shared_review_context,), name="Telegram")

        ftp_process.start()
        tg_process.start()
        review_context_thread.start()

        review_context_thread.join()
        ftp_process.join()
        tg_process.join()
