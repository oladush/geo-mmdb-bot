"""
Кастомный логгер

"""

import logging

class Formatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
    }
    def __init__(self):
        self.log_format = \
            '[%(asctime)s] [%(name)s.%(context)s] %(levelname)s - %(message)s'

        super().__init__(self.log_format)

    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, '\033[0m')
        formatted_levelname = f"{color}{levelname}\033[0m"
        record.levelname = formatted_levelname
        return super().format(record)

class StreamHandler(logging.StreamHandler):
    def __init__(self, level: int, formatter: logging.Formatter):
        super().__init__()
        self.setLevel(level)
        self.setFormatter(formatter)

class Logger(logging.Logger):
    def __init__(self, name: str, level: int, context: str):
        self.context = context
        self.formatter = Formatter()
        self.console_handler = StreamHandler(level, self.formatter)

        super().__init__(name)
        self.setLevel(level)
        self.addHandler(self.console_handler)

    def info(self, msg, *args, **kwargs):
        super().info(msg, extra={'context': self.context},*args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super().error(msg, extra={'context': self.context},*args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super().warning(msg, extra={'context': self.context},*args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        super().debug(msg, extra={'context': self.context},*args, **kwargs)
