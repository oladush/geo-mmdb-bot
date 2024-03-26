import telebot
import requests
from telebot import apihelper
from internal.logger import Logger
from internal.consts import APP_NAME, LOG_LEVEL
from internal.methods import get_md5_hash



def get_inline(geo_base):
    bm = telebot.types.InlineKeyboardMarkup()
    for base in geo_base.data:
        if base != 'actual':
            bm.add(telebot.types.InlineKeyboardButton(text=base, callback_data=base))
    return bm

class TelegramBot(telebot.TeleBot):
    logger = Logger(APP_NAME, LOG_LEVEL, 'telebot')
    def __init__(self, token, handlers=None):
        self.token = token
        super().__init__(token)

    @staticmethod
    def get_inline_geobases(geo_base, command):
        inline_keyboard = telebot.types.InlineKeyboardMarkup()

        for basename, _ in geo_base.data.items():
            if basename != 'actual':
                # в inline добавляются данные
                # в формате <команда>-><имя бд>
                callback_data = f'{command}->{get_md5_hash(basename)}'
                inline_keyboard.add(
                    telebot.types.InlineKeyboardButton(text=basename, callback_data=callback_data)
                )
        return inline_keyboard

    def log_these_handler(self, func):
        def wrapper(message, *args, **kwargs):
            self.logger.info(
                f"user: '{message.from_user.username}' chat_id: '{message.chat.id}' message: '{message.text}'"
            )
            return func(message, *args, **kwargs)

        return wrapper

    def get_update_by_id(self, update_id: int):
        url = f'https://api.telegram.org/bot{self.token}/getUpdates'
        params = {'offset': update_id}
        response = requests.get(url, params=params)
        data = response.json()
        if data['ok']:
            if data['result']:
                return data['result'][0]
            else:
                self.logger.warning("no updates found")
        else:
            self.logger.error(
                f"failed to fetch updates: {data['description']}")

        return {}
