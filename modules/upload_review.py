import json
import requests

from pathlib import Path
from logging import getLogger
from traceback import format_exc

from modules.models.issue import Issue
from keys import ODOO_API_KEY
from settings import ODOO_UPLOAD_ENDPOINT, LOGGER_NAME, ALLOWED_EXTENSIONS


logger = getLogger(LOGGER_NAME)


def upload_review(
    audio_review_path: Path, text_review: str, text_summary: str, issues: list[Issue]
) -> bool:
    try:
        headers = {
            "API-Key": ODOO_API_KEY,
        }

        data = {
            "file_name": audio_review_path.name if audio_review_path is not None else "",
            "transcription": text_review,
            "summary": text_summary,
            "issues": json.dumps([issue.to_dict() for issue in issues]),
        }

        if audio_review_path.suffix in ALLOWED_EXTENSIONS:
            files = {
                "file": open(audio_review_path.absolute().as_posix(), "rb"),
            }
        else:
            files = None

        logger.debug(
            f"Uploading to {ODOO_UPLOAD_ENDPOINT}:\n{data}\n---\nWith file: {audio_review_path}"
        )

        response = requests.post(ODOO_UPLOAD_ENDPOINT, headers=headers, data=data, files=files)

        if response.status_code == 200:
            logger.info("A review has been successfuly uploaded to the remote enpoint")
            return True
        else:
            logger.error(
                f"A review upload has failed: {response.status_code} | Text:\n{response.text}"
            )
            return False

    except KeyboardInterrupt as ex:
        raise ex

    except Exception as ex:
        logger.error(f"Upload failed: {ex} {ex.args}:\n{format_exc}")
        return False
