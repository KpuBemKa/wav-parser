from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer
import whisper
import threading


# the folder in which data from esps is stored
RECORDINGS_FOLDER = "esp-recordings"


class CustomFTP(FTP):
    def __init__(self) -> None:
        super().__init__()

    def ftp_STOR(self, path):
        d = super(CustomFTP, self).ftp_STOR(path)

        def onStorComplete(d):
            if not self.should_transcribe_file(path):
                return d

            folder_path: str = self.shell.filesystemRoot.path.decode() + "\\".join(
                self.workingDirectory
            )

            audio_path = f"{folder_path}\\{path}"
            output_path = f"{folder_path}\\{path.split('.')[:-1][0]}.txt"

            threading.Thread(
                target=self.parse_audio,
                args=[audio_path, output_path],
                daemon=True,
            ).start()

            return d

        d.addCallback(onStorComplete)

        return d

    def parse_audio(self, audio_input_path: str, transcription_output_path: str):
        print(f'Transcribing "{audio_input_path}" audio file...')
        model = whisper.load_model("base")
        result = model.transcribe(audio_input_path)

        file = open(transcription_output_path, "w")
        file.write(str(result["text"]))
        file.close()

        print(f"Trancribed audio:\n{result['text']}")

    def should_transcribe_file(self, file_name: str) -> bool:
        if self.shell.filesystemRoot.basename().decode() != RECORDINGS_FOLDER:
            return False
        
        file_extension = file_name.split(".")[-1:][0]
        if file_extension != "wav" and file_extension != "mp3":
            return False

        return True


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
f.protocol = CustomFTP

reactor.listenTCP(21, f)

print("Starting...")

reactor.run()


# model = whisper.load_model("base")
# result = model.transcribe("vsauce-ted-talk-test.mp3")

# print(result["text"])
# file = open("transcribed.txt", "w+")
# file.write(str(result["text"]))
# file.close()
