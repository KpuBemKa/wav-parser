import pathlib
import logging

LOG_LEVEL = logging.INFO
LOGGER_NAME = "root"
# log message format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"

# the folder in which data from esps is stored
RECORDINGS_FOLDER = "esp-recordings"

# DELETE_CONVERTED_FILES = True
DELETE_CONVERTED_FILES = False

ALLOWED_EXTENSIONS = [".wav", ".mp3", ".ogg"]

ODOO_URL = "http://139.59.88.189:8069"
ODOO_UPLOAD_ENDPOINT = f"{ODOO_URL}/recs/new_rec"

# Path to store audio files
TELEGRAM_AUDIO_DIR = pathlib.Path("./home/telegram-recordings/")
if not TELEGRAM_AUDIO_DIR.exists():
    TELEGRAM_AUDIO_DIR.mkdir()
