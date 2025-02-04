import json
import requests

from pathlib import Path
from logging import getLogger

from modules.models.issue import Issue
from keys import ODOO_API_KEY
from settings import ODOO_UPLOAD_ENDPOINT, LOGGER_NAME


logger = getLogger(LOGGER_NAME)


def upload_review(
    audio_review_path: Path, text_review: str, text_summary: str, issues: list[Issue]
) -> bool:
    # Define the headers (use your access token for authorization)
    headers = {
        "API-Key": ODOO_API_KEY,
    }

    # Prepare the data payload
    data = {
        "file_name": audio_review_path.name if audio_review_path is not None else "",
        "transcription": text_review,
        "summary": text_summary,
        "issues": json.dumps([issue.to_dict() for issue in issues]),
    }

    # Prepare the files payload
    files = (
        {
            "file": open(
                audio_review_path.absolute().as_posix(), "rb"
            ),  # Open the file in binary mode
        }
        if audio_review_path.suffix != ".txt"
        else None
    )

    logger.debug(
        f"Uploading to {ODOO_UPLOAD_ENDPOINT}:\n{data}\n---\nWith file: {audio_review_path}"
    )
    # return True

    # Send the POST request
    response = requests.post(ODOO_UPLOAD_ENDPOINT, headers=headers, data=data, files=files)

    if response.status_code == 200:
        logger.info("A review has been successfuly uploaded to the remote enpoint")
        return True
    else:
        logger.error(
            f"A review upload has failed: {response.status_code} | Text:\n{response.text}"
        )
        return False
