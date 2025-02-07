from pathlib import Path
from logging import getLogger
from threading import Lock, Thread

from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer

from .review_pipeline import ReviewPipeline, UUID, ReviewResult
from .upload_review import upload_review

from settings import RECORDINGS_FOLDER, ALLOWED_EXTENSIONS, LOGGER_NAME


logger = getLogger(LOGGER_NAME)


rv_ctx: ReviewPipeline


class CustomProtocolFTP(FTP):
    def __init__(self) -> None:
        super().__init__()
        self.__result_uuids: dict[UUID, Path] = {}
        self.__results_lock = Lock()
        self.__thread = Thread(target=self.__review_result_watcher, daemon=True)

        self.__thread.start()

    def ftp_STOR(self, path):
        deff = super(CustomProtocolFTP, self).ftp_STOR(path)

        def onStorComplete(deff):
            audio_path = Path(self.shell.filesystemRoot.path.decode()) / path

            if not self.__should_transcribe_file(audio_path):
                return deff

            with self.__results_lock:
                self.__result_uuids[rv_ctx.queue_audio(audio_path)] = audio_path

            return deff

        deff.addCallback(onStorComplete)

        return deff

    def __should_transcribe_file(self, file_path: Path) -> bool:
        if file_path.parent.name != RECORDINGS_FOLDER:
            return False

        if file_path.suffix not in ALLOWED_EXTENSIONS:
            return False

        return True

    def __review_result_watcher(self):
        while True:
            uuids: list[tuple[UUID, ReviewResult]] = []

            with self.__results_lock:
                for _uuid in self.__result_uuids:
                    review_result = rv_ctx.get_result_by_uuid(_uuid)

                    if review_result is not None:
                        uuids.append((_uuid, review_result))

            for _uuid, _review_result in uuids:
                self.__handle_review_result(_review_result, self.__result_uuids[_uuid])

                self.__result_uuids.pop(_uuid)

    def __handle_review_result(
        self,
        review_result: ReviewResult,
        audio_path: Path,
    ):
        if not review_result.completed:
            logger.error("Review result was not completed. Perhaps an error occured.")
            return

        upload_review(
            audio_review_path=audio_path,
            text_review=review_result.corrected_text,
            text_summary=review_result.summary,
            issues=review_result.issues,
        )


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


# Start the FTP server
def start_ftp_server(context: ReviewPipeline):
    global rv_ctx
    rv_ctx = context

    p = Portal(FTPRealm(anonymousRoot="./", userHome="./home"), [CustomDB("static/pass.dat")])

    f = FTPFactory(p)
    f.protocol = CustomProtocolFTP
    f.passivePortRange = range(45_000, 45_010)

    reactor.listenTCP(20021, f)

    logger.info("FTP server has been started on port 20021")

    reactor.run()
