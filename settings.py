import logging

LOG_LEVEL = logging.DEBUG
LOGGER_NAME = "root"
# log message format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"


# the folder in which data from esps is stored
RECORDINGS_FOLDER = "esp-recordings"

DELETE_CONVERTED_FILES = False

ALLOWED_EXTENSIONS = [".wav", ".mp3", ".ogg"]