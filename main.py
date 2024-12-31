from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

import pathlib
from multiprocessing import Process

from modules.audio_transcriber import AudioTranscriber
from modules.log import setup_custom_logger
from settings import LOGGER_NAME, RECORDINGS_FOLDER, ALLOWED_EXTENSIONS
from keys import TELEGRAM_BOT_TOKEN

logger = setup_custom_logger(LOGGER_NAME)


# Define a command for the Telegram bot
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! I am your bot.")


async def help(update: Update, context: CallbackContext):
    await update.message.reply_text("This bot can be used to interact with the FTP server.")


class CustomProtocolFTP(FTP):
    transcriber = AudioTranscriber()

    def __init__(self) -> None:
        super().__init__()

    def ftp_STOR(self, path):
        deff = super(CustomProtocolFTP, self).ftp_STOR(path)

        def onStorComplete(deff):
            audio_path = pathlib.PurePath(self.shell.filesystemRoot.path.decode()) / path

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
def start_ftp_server():
    p = Portal(FTPRealm(anonymousRoot="./", userHome="./home"), [CustomDB("pass.dat")])

    f = FTPFactory(p)
    f.protocol = CustomProtocolFTP
    f.passivePortRange = range(50_000, 50_010)

    reactor.listenTCP(21, f)

    print("Starting...")

    reactor.run()


# Start the Telegram bot in a separate thread
def start_telegram_bot():
    # Initialize Application instead of Updater
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers to the bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))

    # Start polling the bot
    application.run_polling()


def run_telegram_bot():
    start_telegram_bot()


if __name__ == "__main__":
    # Start the FTP server in a separate process
    ftp_process = Process(target=start_ftp_server)
    ftp_process.start()

    # Start the Telegram bot in a separate process
    telegram_process = Process(target=run_telegram_bot)
    telegram_process.start()

    # Wait for both processes to finish (if needed)
    ftp_process.join()
    telegram_process.join()
