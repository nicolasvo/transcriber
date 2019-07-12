import logging
import tempfile
import json
from functools import wraps
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
import speech_recognition as sr
from pydub import AudioSegment

with open("app/res/token.json") as file:
    token = json.load(file)["token"]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

map_language = {
    "english": "en-EN",
    "french": "fr-FR",
    "german": "de-DE",
    "russian": "ru-RU"
}


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


send_typing_action = send_action(ChatAction.TYPING)


def start(update, context):
    keyboard = [[InlineKeyboardButton("English", callback_data='english'),
                 InlineKeyboardButton("French", callback_data='french')],
                [InlineKeyboardButton("German", callback_data='german'),
                 InlineKeyboardButton("Russian", callback_data='russian')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Oh, hello there. Please choose a language:', reply_markup=reply_markup)


def set_language(update, context):
    query = update.callback_query
    context.user_data["language"] = map_language[query.data]
    text = f"Selected language: {query.data.capitalize()}. Forward me a voice message to transcribe."
    query.edit_message_text(text=text)


@send_typing_action
def transcribe(update, context):
    with tempfile.TemporaryDirectory(dir="app/res/") as tmpdirname:
        file_path = f"{tmpdirname}/{update.message.voice.file_id}.ogg"
        audio_file = context.bot.getFile(update.message.voice.file_id)
        audio_file.download(file_path)

        # Convert from opus to flac
        sound = AudioSegment.from_ogg(file_path)
        file_path = file_path[:-4] + ".flac"
        sound.export(file_path, format="flac")

        r = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language=context.user_data["language"])
        logging.info(text)

        context.bot.send_message(chat_id=update.message.chat_id, text=text)


updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
updater.dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(set_language))
dispatcher.add_handler(MessageHandler(Filters.forwarded & Filters.voice, transcribe))
updater.start_polling()
