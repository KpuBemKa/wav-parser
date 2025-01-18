import traceback
import html
import json

from logging import getLogger
from pathlib import Path
from time import time as getTime
from asyncio import run as asyncioRun

from telegram import Update, File, Message
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
    ContextTypes,
)

from . import bot_replies
from modules.reviewing.review_context import ReviewContext
from modules.reviewing.bot_strategy import BotReviewStrategy, UserDialog
from settings import TELEGRAM_AUDIO_DIR, LOGGER_NAME
from keys import TELEGRAM_BOT_TOKEN


logger__ = getLogger(LOGGER_NAME)


class TelegramUserDialog(UserDialog):
    def __init__(self, message: Message) -> None:
        self.__message = message

    def send_message(self, message: str) -> None:
        asyncioRun(self.__message.reply_text(message))

    def send_image(self, image_path: Path) -> None:
        with open(bot_replies.START_ATTACHEMENT_PATH, "rb") as image:
            asyncioRun(self.__message.reply_photo(image, caption=bot_replies.START_REPLY))


async def __start(update: Update, context: CallbackContext):
    if update.message is None:
        logger__.warning("Update does not contain Message", stack_info=True)
        return

    with open(bot_replies.START_ATTACHEMENT_PATH, "rb") as image:
        await update.message.reply_photo(image, caption=bot_replies.START_REPLY)


async def __handle_audio(update: Update, context: CallbackContext):
    if update.message is None:
        logger__.warning("Update does not contain Message", stack_info=True)
        return

    # Get the audio file
    file = update.message.audio or update.message.voice

    # Check if an audio has been uploaded
    if file is None:
        await update.message.reply_text(bot_replies.ATTACHEMENT_DENIED)
        return

    # Start the file download
    file_info_await = context.bot.get_file(file.file_id)

    if update.message.audio:
        # If file is an audio file
        file_name = update.message.audio.file_name
    else:
        # If file is a voice message
        file_name = "voice.ogg"

    if file_name is None:
        await update.message.reply_text(bot_replies.ATTACHEMENT_DENIED)
        return

    # Check if file extension is supported
    file_ext = file_name[file_name.rfind(".") :]
    if file_ext not in [".wav", ".ogg", ".mp3"]:
        await update.message.reply_text(f"{bot_replies.ATTACHEMENT_DENIED}{file_ext}")
        return

    # Get sender's username
    if update.message.from_user:
        username = update.message.from_user.username

    # Make username anonymous if no username was found
    if username is None:
        username = "Anonymous"

    # Make the new file name
    new_file_name = f"tg@{username}_{int(getTime())}{file_ext}"

    # Wait for file info to be received
    file_info: File = await file_info_await

    # Reply to the user that his audio has been received
    reply_await = update.message.reply_text(bot_replies.REVIEW_ACCEPTED)

    # Download the file
    file_path = TELEGRAM_AUDIO_DIR / new_file_name
    await file_info.download_to_drive(file_path.absolute().as_posix())

    # Transcribe it, and upload it
    ReviewContext().handle_audio(BotReviewStrategy(TelegramUserDialog(update.message)), file_path)

    # Wait for the reply to be delivered
    await reply_await


async def __handle_text(update: Update, context: CallbackContext):
    if update.message is None:
        logger__.warning("Update does not contain Message.", stack_info=True)
        return

    if update.message.text is None:
        logger__.warning("Message does not contain any text.", stack_info=True)
        return

    # Reply to the user that his audio has been received
    reply_await = update.message.reply_text(bot_replies.REVIEW_ACCEPTED)

    # Transcribe it, and upload it
    ReviewContext().handle_text(
        BotReviewStrategy(TelegramUserDialog(update.message)), update.message.text
    )

    await reply_await


async def __error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger__.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__ if context.error is not None else None
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    logger__.error(message)

    # # Finally, send the message
    # await context.bot.send_message(
    #     chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    # )


def start_telegram_bot():
    """Starts the Telegram bot in a blocking manner"""

    # Initialize Application instead of Updater
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", __start))
    # application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, __handle_audio))
    application.add_handler(MessageHandler(filters.TEXT, __handle_text))

    application.add_error_handler(__error_handler)

    logger__.info("Telegram bot has been started.")

    # Start polling the bot
    application.run_polling()
