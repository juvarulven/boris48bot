"""
Все что связано с телеграмом
"""
from telebot import TeleBot


class Bot(TeleBot):
    def __init__(self, token):
        super().__init__(token)

    def message_handler(self, handler, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        if content_types is None:
            content_types = ['text']
        handler_dict = self._build_handler_dict(handler,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                content_types=content_types,
                                                **kwargs)
        self.add_message_handler(handler_dict)
        return handler
