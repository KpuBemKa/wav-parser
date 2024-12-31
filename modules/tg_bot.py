import pathlib
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from modules.audio_transcriber import AudioTranscriber
from keys import TELEGRAM_BOT_TOKEN

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