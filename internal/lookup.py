import maxminddb
from unicodedata import lookup

from internal.logger import Logger
from internal.consts import APP_NAME, LOG_LEVEL
from internal.message_wrappers import lookup_message

logger = Logger(APP_NAME, LOG_LEVEL, 'lookup')
@lookup_message
def lookup_ip(ip: str, path_to_db: str):
    try:
        with maxminddb.open_database(path_to_db) as reader:
            data, prefix = reader.get_with_prefix_len(ip)
    except Exception as ex:
        data = {}
        logger.error(str(ex))

    if not data:
        return {}

    return {
        'ip': ip, 'prefix': prefix, 'path_to_db': path_to_db,
        'continent': data.get('continent', {}).get('names', {}).get('en'),
        'country': data.get('country', {}).get('names', {}).get('en'),
        'registered_country': data.get('registered_country', {}).get('names', {}).get('en'),
        'time_zone': data.get('location', {}).get('time_zone'),
        'country_unicode': region_to_unicode(data.get('country', {}).get('iso_code', '')),
        'registered_country_unicode': region_to_unicode(data.get('registered_country', {}).get('iso_code', '')),
    }

def region_to_unicode(region):
    if not region:
        return "❓"
    res = ""
    for s in region:
        res += lookup(f'REGIONAL INDICATOR SYMBOL LETTER {s}')
    return res