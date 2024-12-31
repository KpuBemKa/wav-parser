# import requests
# import base64
# from bs4 import BeautifulSoup
import pathlib
import time

from modules.audio_transcriber import AudioTranscriber
from modules.log import setup_custom_logger
from settings import LOGGER_NAME

logger = setup_custom_logger(LOGGER_NAME)


URL = "http://139.59.88.189:8069"
DB = "reviewer"
USER = "dev@mars.solutions"
PASS = "odooadmin"
API = "b55ad831f7054ca6e6cbffad386b8eedd235a4a7"
API2 = "b55ad831f7054ca6e6cbffad386b8eedd235a4b8"

# File to upload
# file_path = "./home/esp-recordings/esp-recorder_2024-05-19_11-15-18.ogg"
file_path = "./home/esp-recordings/vsauce_test_audio.mp3"

login_url = f"{URL}/web/login"
upload_url = f"{URL}/recs/new_rec"

AudioTranscriber().queue_audio_transcription(pathlib.PurePath(file_path))

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    exit()

# # Start a session
# # session = requests.Session()

# # # First, get the login page to retrieve CSRF token
# # login_page_response = session.get(login_url)

# # # Parse the login page to extract the CSRF token using BeautifulSoup
# # soup = BeautifulSoup(login_page_response.text, "html.parser")
# # csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

# # # Prepare payload for login
# # login_data = {"login": USER, "password": API2, "db": DB, "csrf_token": csrf_token}

# # # Log in to Odoo to establish a session
# # login_response  = session.post(login_url, data=login_data)

# # login_payload = {"login": USER, "password": PASS}
# # login_response = session.post(login_url, data=login_payload)


# # Check if login was successful by inspecting the response
# # if login_response.ok and "success" in login_response.url:
# # print("Login successful")


# def pretty_print_POST(req: requests.PreparedRequest):
#     """
#     At this point it is completely built and ready
#     to be fired; it is "prepared".

#     However pay attention at the formatting used in
#     this function because it is programmed to be pretty
#     printed and may differ from the actual request.
#     """
#     print(
#         "{}\n{}\r\n{}\r\n\r\n{}".format(
#             "-----------START-----------",
#             req.method + " " + req.url,
#             "\r\n".join("{}: {}".format(k, v) for k, v in req.headers.items()),
#             req.body,
#         )
#     )


# # Open the file and send the upload request
# with open(file_path, "rb") as file:
#     files = {"file": (file_path.split("/")[-1], file)}

#     # headers = {
#     #     'X-Requested-With': 'XMLHttpRequest',
#     #     'X-CSRFToken': csrf_token  # Include the CSRF token in the headers
#     # }
#     headers = {
#         "API-Key": API2,
#     }
#     # upload_response = session.post(upload_url, files=files, headers=headers)
#     # upload_response = requests.post(upload_url, files=files, headers=headers)
#     req = requests.Request("POST", upload_url, files=files, headers=headers)
#     prepared = req.prepare()
#     pretty_print_POST(prepared)
#     s = requests.Session()
#     upload_response = s.send(prepared)

# # Print the response
# print(f"Upload Response: {upload_response.text}")
# # else:
# #     print(f"Login failed. Check your credentials:\n{login_response.text}")
