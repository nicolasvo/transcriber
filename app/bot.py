import logging
import tempfile
import json
from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import speech_recognition as sr
from pydub import AudioSegment

with open("app/res/token.json") as file:
    token = json.load(file)["token"]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


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
    text = """
    Hello there,\nForward me a voice message to have it transcribed.
    """
    context.bot.send_message(chat_id=update.message.chat_id, text=text)


@send_typing_action
def transcribe(update, context):
    with tempfile.TemporaryDirectory(dir="app/res/") as tmpdirname:
        # logging.info(tmpdirname)
        file_path = f"{tmpdirname}/{update.message.voice.file_id}.ogg"
        # logging.info(file_path)
        audio_file = context.bot.getFile(update.message.voice.file_id)
        audio_file.download(file_path)

        # Convert from opus to flac
        sound = AudioSegment.from_ogg(file_path)
        file_path = file_path[:-4] + ".flac"
        sound.export(file_path, format="flac")

        r = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ru-RU")
        logging.info(text)

        context.bot.send_message(chat_id=update.message.chat_id, text=text)


updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
audio_handler = MessageHandler(Filters.forwarded & Filters.voice, transcribe)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(audio_handler)

updater.start_polling()
