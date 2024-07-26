from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer

import pathlib

from modules.audio_transcriber import AudioTranscriber
from modules.log import setup_custom_logger
from settings import LOGGER_NAME, RECORDINGS_FOLDER, ALLOWED_EXTENSIONS

logger = setup_custom_logger(LOGGER_NAME)


class CustomProtocolFTP(FTP):
    def __init__(self) -> None:
        super().__init__()
        self.transcriber = AudioTranscriber()

    def ftp_STOR(self, path):
        deff = super(CustomProtocolFTP, self).ftp_STOR(path)

        def onStorComplete(deff):
            audio_path = pathlib.PurePath(self.shell.filesystemRoot.path.decode()) / self.workingDirectory / path
            
            if not self.should_transcribe_file(audio_path):
                return deff
            
            self.transcriber.queue_audio_transcription(audio_path)

            # folder_path: str = self.shell.filesystemRoot.path.decode() + "/".join(
            #     self.workingDirectory
            # )

            # audio_path = f"{folder_path}/{path}"
            # output_path = f"{folder_path}/{self.extract_file_name(path)}.txt"

            # threading.Thread(
            #     target=self.parse_audio,
            #     args=[audio_path, output_path],
            #     daemon=True,
            # ).start()

            return deff

        deff.addCallback(onStorComplete)

        return deff

    def should_transcribe_file(self, file_path: pathlib.PurePath) -> bool:
        if file_path.parent.name != RECORDINGS_FOLDER:
            return False

        if file_path.suffix not in ALLOWED_EXTENSIONS:
            return False

        return True

    # def parse_audio(self, audio_input_path: str, transcription_output_path: str):
    #     try:
    #         print(f"audio path: {audio_input_path}")

    #         # Transcribe audio file into text
    #         print(f'Transcribing "{audio_input_path}" audio file...')

    #         start_time = time.time()

    #         outputs = self.pipe(
    #             audio_input_path,
    #             chunk_length_s=30,
    #             batch_size=24,
    #             return_timestamps=False,
    #         )
    #         end_time = time.time()

    #         # print(f"Trancribed audio:\n{result['text']}")
    #         print(f"Trancribed audio in {end_time - start_time} seconds:\n{outputs['text']}")

    #         # Save transcribed text into a .txt file
    #         with open(transcription_output_path, "w") as file:
    #             file.write(str(outputs["text"]))

    #         # If input file is a .wav, try to convert it to an .ogg,
    #         # because telegram's `sendVoice` command accepts only .mp3, .ogg & .m4a,
    #         # and also because a spectogram of a voice recording can be made only from
    #         # an .ogg file encoded with Opus
    #         if audio_input_path.endswith(".wav"):
    #             print("Audio file is in .wav format. Tying to converting it to .ogg...")
    #             audio_input_path = self.try_convert_wav_to_ogg(audio_input_path)

    #         # Send the audio file into the channel
    #         with open(audio_input_path, "rb") as audio:
    #             payload = {
    #                 "chat_id": TELEGRAM_BOT_CHAT_ID,
    #                 "parse_mode": "HTML",
    #             }
    #             files = {"voice": audio.read()}
    #             response = requests.post(
    #                 f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice",
    #                 data=payload,
    #                 files=files,
    #             )

    #             if not response.ok:
    #                 print(f"Voice message delivery failed. Full response:\n{response.json()}")

    #         # Send the transcribed text to the channel
    #         response = requests.post(
    #             f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
    #             data={
    #                 "chat_id": TELEGRAM_BOT_CHAT_ID,
    #                 "text": f"Transcribed audio:\n{outputs['text']}",
    #                 "parse_mode": "HTML",
    #             },
    #             files=files,
    #         )

    #         if not response.ok:
    #             print(
    #                 f"Message with the transcribed text delivery failed. Full response:\n{response.json()}"
    #             )

    #     except Exception as ex:
    #         print(f"Exception catched: {ex} {ex.args}\n{traceback.format_exc()}")

    # def try_convert_wav_to_ogg(self, wav_path: str) -> str:
    #     """
    #     Tries to convert a .wav file to an .ogg one and normalize the volume.

    #     Returns the path to the converted file in case of success or
    #     the path to the original file in case of errors
    #     """
    #     try:
    #         output_path: str = f"{self.extract_file_name(wav_path)}.ogg"

    #         result: int = os.system(
    #             f'ffmpeg -y -i {wav_path} -c:a libopus -b:a 128k -filter:a "speechnorm" -ac 1 {output_path}'
    #         )

    #         if result != 0:
    #             raise SystemError(f"Unable to convert file '{wav_path}'")

    #         # if the wav file was successfuly converted, no need to store it
    #         pathlib.Path(wav_path).unlink()

    #         return output_path
    #     except SystemError as ex:
    #         print(f"SystemError catched: {ex} {ex.args}\n{traceback.format_exc()}")
    #         return wav_path

    # def extract_file_name(self, file_name: str) -> str:
    #     """
    #     Extract only the file name (exclude the extension) from the file name
    #     Example: `example_file.wav` -> `example_file`
    #     """
    #     return file_name.split(".")[:-1][0]


class CustomDB(FilePasswordDB):
    def __init__(
        self,
        filename,
        delim=b":",
        usernameField=0,
        passwordField=1,
        caseSensitive=True,
        hash=None,
        cache=False,
    ):
        super().__init__(filename, delim, usernameField, passwordField, caseSensitive, hash, cache)

    def getUser(self, username):
        """
        The difference between this `getUser` and `super().getUser()`
        is that `username` encoded from `str` to `bytes` before passing it to `super().getUser()`
        because it searches the file in binary form
        """
        return super().getUser(str.encode(username))

    def requestAvatarId(self, c):
        """
        The difference between this `requestAvatarId` and `super().requestAvatarId()`
        is that password `p` from `self.getUser()` is decoded from `bytes` to `str`
        before comparing it with `c.checkPassword` to comare a `str` with a `str`
        """
        try:
            u, p = self.getUser(c.username)
        except KeyError:
            return defer.fail(error.UnauthorizedLogin())
        else:
            up = credentials.IUsernamePassword(c, None)
            if self.hash:
                if up is not None:
                    h = self.hash(up.username, up.password, p)
                    if h == p:
                        return defer.succeed(u)
                return defer.fail(error.UnauthorizedLogin())
            else:
                return defer.maybeDeferred(c.checkPassword, p.decode()).addCallback(
                    self._cbPasswordMatch, u
                )


p = Portal(FTPRealm(anonymousRoot="./", userHome="./home"), [CustomDB("pass.dat")])

f = FTPFactory(p)
f.protocol = CustomProtocolFTP
f.passivePortRange = range(50_000, 50_010)

reactor.listenTCP(21, f)

print("Starting...")

reactor.run()


# model = whisper.load_model("base")
# result = model.transcribe("vsauce-ted-talk-test.mp3")

# print(result["text"])
# file = open("transcribed.txt", "w+")
# file.write(str(result["text"]))
# file.close()
