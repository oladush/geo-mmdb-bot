import os
import configparser

log_level_map = {
    'INFO': 20,
    'ERROR': 40,
    'WARNING': 30,
    'DEBUG': 10
}

def get_relative_path(file: str):
    # already absolute path
    if file.startswith('/'):
        return file

    dir_path = os.path.dirname(os.path.realpath(__file__))
    relative_path = os.path.join(dir_path, file)

    return relative_path

config_file_path = get_relative_path('../config.ini')
config = configparser.ConfigParser()

config.read(config_file_path)

APP_NAME = config.get('main', 'app_name')
LOG_LEVEL = log_level_map.get(config.get('main', 'log_level'), 20)

FILE_QUEUE = config.get('schema', 'file_queue')
GEO_BASES_MAP_FILE = config.get('schema', 'geo_base_map')
USERS_CAN_LOOKUP_FILE = config.get('schema', 'users_can_lookup')
SECRET = config.get('main', 'secret')
TOKEN = config.get('telegram', 'token')