'''
Бот для лукапа ip адресов из баз данных mmdb
'''
import time
from sys import argv

from internal.logger import Logger

from internal.lookup import lookup_ip

from internal.telebot import TelegramBot, apihelper

from internal.jsondb import \
    GeoBasesDB, UsersDB, QueueDB, State

from internal.methods import \
    get_relative_path, is_valid_ip, is_valid_format, is_zip_archive, \
    is_7z_archive, is_mmdb_database, save_file, file_name_formate, gen_queue_key, print_shreck

from internal.message_wrappers import help_message

from internal.consts import \
    APP_NAME, SECRET, LOG_LEVEL, USERS_CAN_LOOKUP_FILE, GEO_BASES_MAP_FILE, FILE_QUEUE, TOKEN

from internal.unzipper import Zip, SevenZip

logger = Logger(APP_NAME, LOG_LEVEL, 'main')

@help_message
def get_help():
    return {
        'help': 'to print these message',
        'login': 'to auth in these bot (use invite codes)',
        'set': 'to select exist db or upload new',
        'gen_invite': 'to generate invite code',
        'message': 'for lookup ip addresses just send it to bot'
    }

def run_app():
    print_shreck()
    logger.info(f'{APP_NAME} has been started')

    users_db = UsersDB(
        get_relative_path(USERS_CAN_LOOKUP_FILE, __file__), secret=SECRET)
    
    geo_bases_db = GeoBasesDB(
        get_relative_path(GEO_BASES_MAP_FILE, __file__)
    )

    file_queue = QueueDB(
        get_relative_path(FILE_QUEUE, __file__)
    )

    # если необходимо сбросить схему или ее часть
    if '--drop-geo' in argv or '--drop-all' in argv:
        geo_bases_db.clean()
    if '--drop-users' in argv or '--drop-all' in argv:
        users_db.clean()
    if '--drop-queue' in argv or '--drop-all' in argv:
        file_queue.clean()

    if users_db.is_empty() or '--gen-invite' in argv:
        invite = users_db.generate_invite(SECRET)
        logger.warning(f'has not found users in db. use invite: {invite}')

    telebot = TelegramBot(token=TOKEN)

    # handlers
    @telebot.message_handler(commands=['login'])
    @telebot.log_these_handler
    def authorization(message):
        """
        Метод используемый для авторизации
        После ввода комманды /admin бот ожидает инвайт код
        """
        telebot.send_message(
            message.chat.id,
            text="🖖Wasap.Enter your invite code here",
        )
        users_db.data[str(message.chat.id)] = State.WAITING.value
        users_db.push()

    @telebot.message_handler(
        content_types=['text'],
        func=lambda message: not users_db.is_authorized(message.chat.id))
    @telebot.log_these_handler
    def auth_text_handler(message):
        '''
        Хендлер ожидает ввод инвайт кода от пользователя
        и авторизует его если он корректен
        '''
        probably_invite = message.text.strip()
        if users_db.is_waiting(message.chat.id):
            if users_db.verify_invite_code(probably_invite, SECRET):
                telebot.send_message(
                    message.chat.id,
                    text="Authorization successful 🔥",
                )
                users_db.authorize(message.chat.id, probably_invite)
                logger.info(
                    f'user {message.from_user.username} has been authorized'
                )
            else:
                telebot.send_message(
                    message.chat.id,
                    text="Invite code is incorrect 💀",
                )
                logger.warning(
                    f'invite code {probably_invite} is incorrect. user {message.from_user.username}'
                )
        else:
            telebot.send_message(
                message.chat.id,
                text="You are not authorized. Enter command /login to login here",
            )

    @telebot.message_handler(commands=['gen_invite'])
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def gen_invite(message):
        '''
        Хендлер генерирует invite код для приглашения других пользователей
        '''
        invite_code = users_db.generate_invite(SECRET)

        telebot.send_message(
            message.chat.id,
            text=f"Your invite code: {invite_code}. Share it",
        )

        logger.info(
            f'user {message.from_user.username} '
            f'generated invite code: {invite_code}'
        )


    @telebot.message_handler(commands=['set'])
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def set_database(message):
        '''
        Хендлер для переключения БД
        Отправляет пользователю inline-keyboard
        '''
        telebot.send_message(
            message.chat.id,
            text="Choose filename or upload new file 👇",
            reply_markup=telebot.get_inline_geobases(geo_bases_db, 'set')
        )
        geo_bases_db.set_wait_actual()

    @telebot.message_handler(commands=['del'])
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def set_database(message):
        '''
        Хендлер для переключения БД
        Отправляет пользователю inline-keyboard
        '''
        telebot.send_message(
            message.chat.id,
            text="Choose filename or upload new file 👇",
            reply_markup=telebot.get_inline_geobases(geo_bases_db, 'del')
        )
        geo_bases_db.set_wait_actual()

    @telebot.callback_query_handler(func=lambda call: 'set' in call.data.split('->'))
    def handle_query_set(call):
        '''
        Хендлер перехватывает запросы callback c командой set
        из inline-keyboard и устанавливает активную геобазу
        '''
        if geo_bases_db.is_wait_actual():
            command, data, *_ = call.data.split('->')
            db_name, _ = geo_bases_db.get_by_md5(data)

            has_been_set = False

            if db_name:
                has_been_set = geo_bases_db.set_actual(db_name)

            if has_been_set:
                telebot.send_message(call.from_user.id, '🤟Geo base successfully installed!')
            else:
                telebot.send_message(call.from_user.id, "💀File is not exist")
        else:
            telebot.send_message(call.from_user.id, "💀Don't touch me! Use /set")


    @telebot.callback_query_handler(func=lambda call: 'del' in call.data.split('->'))
    def handle_query_del(call):
        '''
        Хендлер перехватывает запросы callback c командой del
        из inline-keyboard и удаляет выбранную геобазу
        '''
        if geo_bases_db.is_wait_actual():
            command, data, *_ = call.data.split('->')
            db_name, _ = geo_bases_db.get_by_md5(data)

            has_been_deleted = False

            if db_name:
                has_been_deleted = geo_bases_db.remove(db_name)

            if has_been_deleted:
                telebot.send_message(call.from_user.id, '🤟Geo base successfully deleted!')
            else:
                telebot.send_message(call.from_user.id, "💀File is not exist")
        else:
            telebot.send_message(call.from_user.id, "💀Don't touch me! Use /set")

    @telebot.message_handler(
        content_types=['text'],
        func=lambda message: is_valid_ip(message.text))
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def lookup_handler(message):
        '''
        Хендлер ожидает на вход ip адрес для лукапа
        '''
        path_to_mmdb = geo_bases_db.get_actual_db()

        if not path_to_mmdb:
            logger.error('actual database has not been set')
            lookup_result = '💀Actual database has not been set. Use /set'

        else:
            lookup_result = lookup_ip(message.text, path_to_mmdb)

        telebot.send_message(
            message.chat.id,
            text=lookup_result
        )

    @telebot.message_handler(
        func=lambda message: is_valid_format(message.document.file_name),
        content_types=['document'])
    @users_db.handle_if_authorized
    def upload_geo_handler(message):
        '''
        Хендлер ожидает на вход файлы формата mmdb, 7z и zip
        Загружает и сохраняет гео дата базы
        '''

        has_been_saved = False

        if geo_bases_db.is_wait_actual():
            try:
                file_info = telebot.get_file(message.document.file_id)
                logger.info(f'user {message.from_user.username} upload file {file_info}')

            except apihelper.ApiTelegramException as ex:
                logger.error(str(ex))
                telebot.send_message(message.chat.id,
                    text='☠️ File is too big. You can send zip or 7z (separation supported) file.')
                return

            raw_file = telebot.download_file(file_info.file_path)

            if is_mmdb_database(raw_file):
                logger.info('uploaded file is a mmdb')
                new_file_name = file_name_formate(
                    message.document.file_name
                )
                save_to = get_relative_path(
                    f'bases/{new_file_name}', __file__
                )

                has_been_saved = save_file(save_to, raw_file)

                if has_been_saved:
                    geo_bases_db.upload_mmdb(
                        new_file_name, f'bases/{new_file_name}'
                    )

            elif is_7z_archive(raw_file):
                logger.info('uploaded file is a 7zip')
                key = gen_queue_key(message.chat.id, message.date)
                file_queue.add_file(
                    key, message.document.file_name, raw_file
                )

                if file_queue.probably_ready(key):
                    files_from_zip = SevenZip.unzip(file_queue.get_path_to_archive(key))

                    file_to_set = ''

                    if files_from_zip:
                        file_queue.delete(key)

                    for file_name, file_bytes in files_from_zip.items():
                        if is_mmdb_database(file_bytes):
                            logger.info(f'{file_name} is mmdb. file has been saved')

                            new_file_name = file_name_formate(
                                file_name
                            )
                            save_to = get_relative_path(
                                f'bases/{new_file_name}', __file__
                            )

                            has_been_saved = save_file(save_to, file_bytes)

                            if has_been_saved:
                                geo_bases_db.upload_mmdb(
                                    new_file_name, f'bases/{new_file_name}'
                                )
                                file_to_set = new_file_name

                    if file_to_set:
                        geo_bases_db.set_actual(file_to_set)

            elif is_zip_archive(raw_file):
                logger.info('uploaded file is a zip')

                files_from_zip = Zip.unzip(raw_file)

                file_to_set = ''

                for file_name, file_bytes in files_from_zip.items():
                    if is_mmdb_database(file_bytes):
                        logger.info(f'{file_name} is mmdb. file has been saved')

                        new_file_name = file_name_formate(
                            file_name
                        )
                        save_to = get_relative_path(
                            f'bases/{new_file_name}', __file__
                        )

                        has_been_saved = save_file(save_to, file_bytes)

                        if has_been_saved:
                            geo_bases_db.upload_mmdb(
                                new_file_name, f'bases/{new_file_name}'
                            )
                            file_to_set = new_file_name

                if file_to_set:
                    geo_bases_db.set_actual(file_to_set)

            if has_been_saved:
                telebot.send_message(
                    message.chat.id, f'{message.document.file_name} has been uploaded 🔥'
                )

    @telebot.message_handler(content_types=['document'])
    @users_db.handle_if_authorized
    def incorrect_document_handler(message):
        '''
        Хендлер для отбивки о том, что пришел файл с неразраешенным форматом
        '''

        logger.warning(
            f'user {message.from_user.username} '
            f'send file with not allowed format: {message.document.file_name}'
        )
        telebot.send_message(
            message.chat.id,
            text='☠️ File has unknown format. Allowed formats: .zip, .7z, .mmdb'
        )

    @telebot.message_handler(content_types=['text'])
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def help_handler(message):
        telebot.send_message(
            message.chat.id,
            text=get_help()
        )

    @telebot.message_handler(commands=['help'])
    @telebot.log_these_handler
    @users_db.handle_if_authorized
    def other_text_handler(message):
        telebot.send_message(
            message.chat.id,
            text=get_help()
        )

    telebot.infinity_polling()


if __name__ == '__main__':
    run_app()
