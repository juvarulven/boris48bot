"""
Все что связано с телеграмом
"""
import re
from telebot import TeleBot, util, apihelper
from database import Database
from config import BOT_OWNER_ID

apihelper.ENABLE_MIDDLEWARE = True


class Bot(TeleBot):
    def __init__(self, token: str):
        """
        :param token: токен телеграм-бота
        """
        super().__init__(token)
        self.db = Database('users')
        self._users = {}
        self.default_middleware_handlers.append(self._middleware)
        self._load_users()

    def _load_users(self):
        """
        Загружает список юзеров из БД
        :return:
        """
        users = self.db.get_document_names()
        for user_id in users:
            self._users[user_id] = self.db.get_document(user_id)

    def _middleware(self, _, message):
        """
        Добавляет каждого впервые написавшего боту пользователя в список self._users и в БД коллекцию 'users'.
        (потому что данные -- это новое золото!)
        На самом деле нет. Это чтобы access_level'ы хранить в основном...
        :param _:
        :param message:
        :return:
        """
        message = message.message
        user_info = {}
        user_id = str(message.from_user.id)
        is_bot = message.from_user.is_bot
        if user_id not in self._users:
            user_info['username'] = message.from_user.username
            user_info['first_name'] = message.from_user.first_name
            user_info['last_name'] = message.from_user.last_name
            user_info['is_bot'] = is_bot
            if is_bot:
                user_info['access_level'] = 0
            elif str(BOT_OWNER_ID) == user_id:
                user_info['access_level'] = 2
            else:
                user_info['access_level'] = 1
            self._users[user_id] = user_info
            self.db.update_document(user_id, fields_with_content=user_info)
            self.db.save_and_update()

    def message_handler_method(self, handler, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Публичный метод, повторяющий функциональность декоратора message_handler

        :param handler: функция-обрабатчик сообщений из Телеграма
        :param commands: список команд для реагирования
        :param regexp: регулярное выражение
        :param func: место под lambda-функцию. Если она вернет True,
        обработчик будет вызван
        :param content_types: список типов сообщений для реагирования.
        по умолчанию ['text']
        :param kwargs:
        :return: функция, переданная как handler
        """
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

    def load_command_plugins(self, plugins_list: list) -> None:
        """
        Загрузка плагинов-обработчиков комманд из телеграма через self.message_handler()

        :param plugins_list: список словарей вида [{'handler': функция-обработчик, 'command': ['команда'...]}...]
        :return: None
        """
        while plugins_list:
            plugin = plugins_list.pop()
            assert isinstance(plugin, dict), \
                'список плагинов содержит не словари: ' + repr(plugin)
            assert len(plugin) == 3, \
                'в словаре плагина неправильное число элементов: ' + repr(plugin)
            assert hasattr(plugin['handler'], '__call__'), \
                'в словаре плагина по ключу "function" содержится не функция: ' + repr(plugin)
            assert isinstance(plugin['commands'], list), \
                'в словаре плагина по ключу "commands" содержится не список: ' + repr(plugin)
            assert all(list(map(lambda type_of: isinstance(type_of, str), plugin['commands']))), \
                'в списке "commands" словаря плагина содержатся не строки: ' + repr(plugin)
            self.message_handler_method(plugin['handler'],
                                        commands=plugin['commands'],
                                        access_level=plugin['access_level'])

    def _test_filter(self, message_filter, filter_value, message):
        """
        Test filters
        Переопределен, чтобы добавить фильтр access_level
        :param message_filter:
        :param filter_value:
        :param message:
        :return:
        """
        test_cases = {
            'content_types': lambda msg: msg.content_type in filter_value,
            'regexp': lambda msg: msg.content_type == 'text' and re.search(filter_value, msg.text, re.IGNORECASE),
            'commands': lambda msg: msg.content_type == 'text' and util.extract_command(msg.text) in filter_value,
            'func': lambda msg: filter_value(msg),
            'access_level': lambda msg: self._users[str(msg.from_user.id)]['access_level'] >= filter_value
        }

        return test_cases.get(message_filter, lambda msg: False)(message)

    def get_user_access_level(self, user_id: int) -> int:
        return self._users[str(user_id)]['access_level']

    def get_users(self) -> dict:
        return self._users.copy()
