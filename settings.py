from pathlib import Path
from logging import DEBUG as logging_DEBUG
# from logging import INFO as loggin_INFO

# LOG_LEVEL = loggin_INFO
LOG_LEVEL = logging_DEBUG
LOGGER_NAME = "logging"

# log message format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"

# the folder in which data from esps is stored
RECORDINGS_FOLDER = "esp-recordings"

# DELETE_CONVERTED_FILES = True
DELETE_CONVERTED_FILES = False

ALLOWED_EXTENSIONS = [".wav", ".mp3", ".ogg"]

ODOO_URL = "http://139.59.88.189:8069"
ODOO_UPLOAD_ENDPOINT = f"{ODOO_URL}/revw/new_rec"

# Path to store audio files
TELEGRAM_AUDIO_DIR = Path("./home/telegram-recordings/")
if not TELEGRAM_AUDIO_DIR.exists():
    TELEGRAM_AUDIO_DIR.mkdir()
