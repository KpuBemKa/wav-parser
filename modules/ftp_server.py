from pathlib import Path
from logging import getLogger
from traceback import format_exc

from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor

from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP

# from twisted.protocols.ftp import FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer

from modules.reviewing.review_context import ReviewQueues
from modules.reviewing.device_strategy import DeviceStrategy

from settings import RECORDINGS_FOLDER, ALLOWED_EXTENSIONS, LOGGER_NAME


logger = getLogger(LOGGER_NAME)


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


class CustomFtpProtocol(FTP):
    def __init__(self, review_queues: ReviewQueues) -> None:
        super().__init__()
        self.__review_queues = review_queues

    def ftp_STOR(self, path):
        deff = super(CustomFtpProtocol, self).ftp_STOR(path)

        def onStorComplete(deff):
            try:
                audio_path = Path(self.shell.filesystemRoot.path.decode()) / path

                if not self.should_transcribe_file(audio_path):
                    return deff

                self.__review_queues.audio_queue.put((DeviceStrategy(), audio_path))

            except Exception as ex:
                logger.error(
                    f"Exception catched durint audio transcription: {ex} {ex.args}\n{format_exc()}"
                )
                return None

            return deff

        deff.addCallback(onStorComplete)

        return deff

    def should_transcribe_file(self, file_path: Path) -> bool:
        if file_path.parent.name != RECORDINGS_FOLDER:
            return False

        if file_path.suffix not in ALLOWED_EXTENSIONS:
            return False

        return True


class CustomFtpFactory(FTPFactory):
    def __init__(
        self,
        review_queues: ReviewQueues,
        portal=None,
        userAnonymous="anonymous",
    ):
        super().__init__(portal, userAnonymous)
        self.__review_queues = review_queues

    # def __init__(self) -> None:
    #     super().__init__()
    # def __init__(self, review_context: ReviewQueues):
    #     self.review_context = review_context

    def buildProtocol(self, addr):
        return CustomFtpProtocol(self.__review_queues)


class FtpServer:
    def __init__(self, review_queues: ReviewQueues) -> None:
        self.__review_queues = review_queues

        portal = Portal(
            FTPRealm(anonymousRoot="./", userHome="./home"), [CustomDB("static/pass.dat")]
        )

        self.__factory = CustomFtpFactory(self.__review_queues, portal=portal)
        # f.protocol = CustomFtpProtocol
        self.__factory.passivePortRange = range(45_000, 45_010)

    def run_ftp_server(self):
        logger.info("FTP server has been started on port 20021")

        reactor.listenTCP(20021, self.__factory)
        reactor.run()
