from multiprocessing import Process, Manager

from modules.bots.tg_bot import TelegramBot
from modules.ftp_server import FtpServer
from modules.log import setup_custom_logger
from modules.reviewing.review_context import ReviewQueues, ReviewContext
from settings import LOGGER_NAME


logger = setup_custom_logger(LOGGER_NAME)


if __name__ == "__main__":
    with Manager() as manager:
        review_queues = ReviewQueues()
        review_queues.audio_queue = manager.Queue()
        review_queues.text_queue = manager.Queue()
    
        review_process = Process(target=ReviewContext(review_queues).run_reviewing, name="Reviewing")
        review_process.start()

        ftp_process = Process(target=FtpServer(review_queues).run_ftp_server, name="FTP")
        ftp_process.start()

        telegram_process = Process(
            target=TelegramBot(review_queues).run_telegram_bot, name="Telegram bot"
        )
        telegram_process.start()

        # Wait for all processes to finish
        ftp_process.join()
        telegram_process.join()
        review_process.join()
