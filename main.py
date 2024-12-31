import pathlib
import threading
import subprocess

from twisted.cred.checkers import FilePasswordDB
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.protocols.ftp import FTPFactory, FTPRealm, FTP
from twisted.cred import credentials, error
from twisted.internet import defer

from modules.tg_bot import start_bot
from modules.audio_transcriber import AudioTranscriber
from modules.log import setup_custom_logger
from settings import LOGGER_NAME, RECORDINGS_FOLDER, ALLOWED_EXTENSIONS


logger = setup_custom_logger(LOGGER_NAME)


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



# Path to store audio files
AUDIO_DIR = pathlib.Path("./home/telegram-recordings/")


# Define the bot functionality
async def __start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me an audio message, and I'll store it as a file.")


async def __handle_audio(update: Update, context: CallbackContext):
    if update.message is None:
        return

    # Get the audio file
    file = update.message.audio or update.message.voice

    if file is None:
        await update.message.reply_text("I can accept only audio messages.")
        return

    file_id = file.file_id
    file_info = await context.bot.get_file(file_id)
    file_name = f"{file_id}.ogg"  # Use .ogg for voice messages, modify as needed

    # Download the file
    file_path = AUDIO_DIR / file_name
    await file_info.download_to_drive(file_path.absolute().as_posix())

    AudioTranscriber().queue_audio_transcription(file_path)


def start_bot():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", __start))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == "__main__":
    start_bot()


if __name__ == "__main__":
    threading.Thread(target=launch_bot).start()
    logger.info("Telegram bot has been launched.")
    
    p = Portal(FTPRealm(anonymousRoot="./", userHome="./home"), [CustomDB("pass.dat")])

    f = FTPFactory(p)
    f.protocol = CustomProtocolFTP
    f.passivePortRange = range(45_000, 45_010)

    reactor.listenTCP(20021, f)

    logger.info("Starting FTP server...")

    reactor.run()