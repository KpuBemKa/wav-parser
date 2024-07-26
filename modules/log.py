import logging

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

from settings import LOG_LEVEL, LOG_FORMAT


def setup_custom_logger(name):
    formatter = logging.Formatter(fmt=LOG_FORMAT)

    # file_handler = logging.FileHandler(LOG_FILE)
    # file_handler = CustomTimedRotatingFileHandler("logs/eld-log.log", when="midnight", delay=True)
    # file_handler = CustomTimedRotatingFileHandler("logs/eld-log.log", when="S", interval=10, delay=True)
    # file_handler = ConcurrentTimedRotatingFileHandler("logs/eld-log.log", when="S", interval=10, delay=True)
    file_handler = ConcurrentTimedRotatingFileHandler(
        "logs/transcriber.log", when="midnight", delay=True
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
