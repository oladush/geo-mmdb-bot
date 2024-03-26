import os
import json

import hmac
import secrets
import hashlib

from enum import Enum

from internal.logger import Logger
from internal.consts import APP_NAME, LOG_LEVEL
from internal.methods import get_md5_hash
from internal.unzipper import SevenZip

class State(Enum):
    WAITING = 'waiting'

class JsonDB:
    logger = Logger(APP_NAME, LOG_LEVEL, 'db')
    def __init__(self, file):
        self.file = file
        self.data = {}
        self.pull()

    def remove(self, key):
        if key not in self.data:
            self.logger.error(f'entry with key: {key} not in db')
            return False

        self.logger.info(f'remove entry with key: {key}')
        del self.data[key]
        return True

    def pull(self):
        """
        Обновить данные из файла
        :return:
        """
        self.logger.info(f'pull data from {self.file}')
        with open(self.file, 'r') as rdb:
            self.data = json.load(rdb)

    def push(self):
        """
        Сохранить данные в файл
        :return:
        """
        self.logger.info(f'push data to {self.file}')
        with open(self.file, 'w') as wdb:
            json.dump(self.data, wdb)

    def is_empty(self):
        return not self.data

    def clean(self):
        self.logger.info(f'data has been cleaned {self.file}')
        self.data = {}
        self.push()

    def get(self, key):
        return self.data.get(key)

    def get_by_md5(self, hash):
        for key, item in self.data.items():
            if get_md5_hash(key) == hash:
                return key, item
        return None, None


class UsersDB(JsonDB):
    logger = Logger(APP_NAME, LOG_LEVEL, 'users')
    def __init__(self, file, secret):
        self.secret = secret
        super().__init__(file)

    def authorize(self, client_id: int, code):
        self.data[str(client_id)] = code
        self.push()

    def is_authorized(self, client_id: int):
        return self.verify_invite_code(
            self.data.get(str(client_id), ''),
            self.secret
        )

    def is_waiting(self, client_id: int):
        return self.data.get(str(client_id), '') == State.WAITING.value

    def set_waiting(self, client_id):
        self.data[str(client_id)] = State.WAITING.value

    def handle_if_authorized(self, func):
        def wrapper(message):
            if not self.is_authorized(message.chat.id):
                self.logger.warning(
                    f"authentication error. user {message.from_user.username}:{message.chat.id} can't use these app")
                return None
            return func(message)

        return wrapper

    @staticmethod
    def generate_invite(secret: str):
        secret_bytes = secret.encode()
        random_bytes = secrets.token_urlsafe(16).encode()
        hmac_code = hmac.new(secret_bytes, random_bytes, hashlib.sha256).hexdigest()
        return random_bytes.decode() + hmac_code[:8]

    @staticmethod
    def verify_invite_code(invite_code, secret_key):
        random_bytes = invite_code[:-8]
        hmac_code = invite_code[-8:]
        expected_hmac = hmac.new(secret_key.encode(), random_bytes.encode(), hashlib.sha256).hexdigest()[:8]
        return hmac.compare_digest(expected_hmac, hmac_code)


class GeoBasesDB(JsonDB):
    logger = Logger(APP_NAME, LOG_LEVEL, 'geo-bases')

    def set_actual(self, dbname):
        if dbname not in self.data:
            self.logger.error(f'geobase "{dbname}" is not exist')
            return False

        self.data['actual'] = dbname
        self.logger.info(f'geobase "{dbname}:{self.data[dbname]}" has been seted')
        self.push()
        return True
    def set_wait_actual(self):
        self.data['actual'] = State.WAITING.value
        self.logger.info('attempt to changing geo db')
        self.push()

    def is_wait_actual(self):
        return self.data.get('actual') == State.WAITING.value

    def get_actual_db(self):
        if self.is_wait_actual():
            return None

        return self.data.get(self.data.get('actual'))

    def upload_mmdb(self, alias: str, file_path: str):
        self.logger.info(f'{alias}:{file_path} has been loaded')
        self.data[alias] = file_path
        self.push()

    def remove(self, key):
        if key == self.get_actual_db():
            self.logger.info("can't remove actual db. set other")
            return False
        return super().remove(key)

class QueueDB(JsonDB):
    logger = Logger(APP_NAME, LOG_LEVEL, 'file-queue')
    def add(self, key, value):
        if key not in self.data:
            self.data[key] = []
        self.logger.error(f'value:{value} has been added to queue with id:{key}')
        self.data[key].append(value)
        self.push()

    def add_file(self, key, filename, raw_data):
        tmp_save_to = f'.tmp/{key}'
        os.makedirs(tmp_save_to, exist_ok=True)

        file_saved_to = f'{tmp_save_to}/{filename}'
        with open(file_saved_to, 'wb') as wf:
            wf.write(raw_data)

        self.add(key, file_saved_to)

    def delete(self, key):
        if key not in self.data:
            self.logger.info(f'queue with id:{key} not in db')
            return
        del self.data[key]
        self.push()

    def get_path_to_archive(self, key):
        try:
            return os.path.dirname(self.data.get(key, [])[0])
        except IndexError:
            return None
    def probably_ready(self, key):
        try:
            path_to_archive = os.path.dirname(self.data.get(key, [])[0])
        except IndexError:
            return False

        return SevenZip.is_ready(path_to_archive)
