from unicodedata import lookup
from datetime import datetime
import maxminddb
import telebot
import hashlib
import json
import re


class JsonDB:
    def __init__(self, file):
        self.file = file
        self.data = None
        self.get_from_file()

    def get_from_file(self):
        with open(self.file, 'r') as rdb:
            self.data = json.load(rdb)
            rdb.close()

    def set_to_file(self):
        with open(self.file, 'w') as wdb:
            json.dump(self.data, wdb)
            wdb.close()


ip_reg = "([0-9]{1,3}[\.]){3}[0-9]{1,3}"
token = '5514539670:AAHAet9fB5p_uzn5b8Pp4o4hnlOEm3ZWYoU'
secret = '1dc1b623edf28a915ebe6d94cb79033a9263c9839def802c249af15e19e3c20f'

hash_of_secret = 'c959fccda504b3bb8610e3764a28f72fd71b7b7374a3adbea39735eac5154872'
path = "/usr/local/bots/ptaf_mmdb/"

print(hashlib.sha256(secret.encode()).hexdigest())

bot = telebot.TeleBot(token)
db = JsonDB(path + 'database.json')
mmdb = JsonDB(path + 'geobases.json')

def authorize(message):
    db.data[str(message.chat.id)] = hashlib.sha256(hashlib.sha256(message.text.encode()).hexdigest().encode()).hexdigest()
    db.set_to_file()

def list_of_geobases():
    bm = telebot.types.InlineKeyboardMarkup()
    for base in mmdb.data:
        if base != 'actual':
            bm.add(telebot.types.InlineKeyboardButton(text=base, callback_data=base))
    return bm

def authorized(message):
    client_id = str(message.chat.id)
    if client_id in db.data:
        return hashlib.sha256(hash_of_secret.encode()).hexdigest() == db.data[client_id]
    return False

def region_to_unicode(region):
    if not region:
        return "❓"
    res = ""
    for s in region:
        res += lookup(f'REGIONAL INDICATOR SYMBOL LETTER {s}')
    return res

def get_info_about_ip(ip):
    with maxminddb.open_database(mmdb.data['actual']) as reader:
        data, prefix = reader.get_with_prefix_len(ip)

    print(data)

    if not data:
        return "Not found("

    if 'location' not in data:
        data['location'] = {}
        data['location']['time_zone'] = "❓"

    text = f""" Result from {mmdb.data['actual'].split('s/')[-1]}
    ip: {ip}/{prefix}
    Continent: {data['continent']['names']['en']}
    Country: {data['country']['names']['en']} {region_to_unicode(data['country']['iso_code'])}
    Registered country: {data['registered_country']['names']['en']} {region_to_unicode(data['registered_country']['iso_code'])}
    Time zone: {data['location']['time_zone']}

    https://www.abuseipdb.com/check/{ip}
    """
    return text

@bot.message_handler(commands=['admin'])
def authorization(message):
    db.data[str(message.chat.id)] = 'waiting'
    db.set_to_file()

@bot.message_handler(commands=['set'])
def set_database(message):
    if authorized(message):
        bot.send_message(message.chat.id, "Please choose filename from list or upload new file", reply_markup=list_of_geobases())
        mmdb.data['actual'] = 'waiting'
        mmdb.set_to_file()

@bot.message_handler(content_types=['text'])
def text_handler(message):
    client_id = str(message.chat.id)
    if client_id in db.data:
        if hashlib.sha256(hash_of_secret.encode()).hexdigest() == db.data[client_id]:
            match = re.search(ip_reg, message.text)
            if match:
                bot.send_message(message.chat.id, get_info_about_ip(match.group()))

        elif db.data[client_id] == 'waiting':
            authorize(message)

@bot.message_handler(content_types=['document'])
def load_geo(message):
    if authorized(message) and mmdb.data['actual'] == 'waiting':
        file_info = bot.get_file(message.document.file_id)
        raw_file = bot.download_file(file_info.file_path)

        file_name = f'_{datetime.now().strftime("%Y-%m-%d-%H-%M")}_' + message.document.file_name

        with open(path + 'bases/' + file_name, 'wb') as wf:
            wf.write(raw_file)
            wf.close()

        bot.send_message(message.chat.id, 'Success uploaded!')

        mmdb.data['actual'] = path + 'bases/' + file_name
        mmdb.data[file_name] = path + 'bases/' + file_name
        mmdb.set_to_file()

        bot.send_message(message.chat.id, 'Geo base successfully installed!')

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # if call.from_user.id == CHAT_ID:
    if mmdb.data['actual'] == 'waiting':
        try:
            mmdb.data['actual'] = mmdb.data[call.data]
            mmdb.set_to_file()

            bot.send_message(call.from_user.id, 'Geo base successfully installed!')
        except ValueError:
            bot.send_message(call.from_user.id, "file is not exist")
    else:
        bot.send_message(call.from_user.id, "dont touch me! enter /set")

bot.infinity_polling()
