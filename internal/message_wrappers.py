'''
Подмодуль содержит шаблоны сообщений ответов бота
'''

def lookup_message(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if not result:
            return "Ip has not been founded 👀"

        return f""" Result from {result.get('path_to_db')}
            ip: {result.get('ip')}/{result.get('prefix')}
            Continent: {result.get('continent')}
            Country: {result.get('country')} {result.get('country_unicode')}
            Registered country: {result.get('registered_country')} {result.get('registered_country_unicode')}
            Time zone: {result.get('time_zone')}

            https://www.abuseipdb.com/check/{result.get('ip')}
            """.replace('None', '❓')

    return wrapper

def help_message(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if not result:
            return ""

        return f""" 
            Commands: 
{'\n'.join([f'/{command} - {description}' for command, description in result.items() if command != 'message'])}
              
{result.get('message', '')}
            """

    return wrapper