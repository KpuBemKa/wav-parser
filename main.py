from multiprocessing import Process

from modules.tg_bot import start_telegram_bot
from modules.ftp_server import start_ftp_server
from modules.log import setup_custom_logger

from settings import LOGGER_NAME


logger = setup_custom_logger(LOGGER_NAME)


if __name__ == "__main__":
    # Start the FTP server in a separate process
    ftp_process = Process(target=start_ftp_server)
    ftp_process.start()

    # Start the Telegram bot in a separate process
    telegram_process = Process(target=start_telegram_bot)
    telegram_process.start()

    # Wait for both processes to finish (if needed)
    ftp_process.join()
    telegram_process.join()
