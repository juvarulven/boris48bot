"""
Все что связано с телеграмом
"""
from telebot import TeleBot


class Bot(TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.database_lock = False

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
            assert len(plugin) == 2, \
                'в словаре плагина неправильное число элементов: ' + repr(plugin)
            assert hasattr(plugin['handler'], '__call__'), \
                'в словаре плагина по ключу "function" содержится не функция: ' + repr(plugin)
            assert isinstance(plugin['commands'], list), \
                'в словаре плагина по ключу "commands" содержится не список: ' + repr(plugin)
            assert all(list(map(lambda type_of: isinstance(type_of, str), plugin['commands']))), \
                'в списке "commands" словаря плагина содержатся не строки: ' + repr(plugin)
            self.message_handler_method(plugin['handler'], commands=plugin['commands'])

    def _exec_task(self, task, *args, **kwargs):
        """
        Переопределенный метод из класса TeleBot
        Костыль, вбитый для того, чтобы плагины получали доступ к объекту бота
        :param task: функция (хендлер)
        :param args:
        :param kwargs:
        :return:
        """
        if self.threaded:
            self.worker_pool.put(task, self, *args, **kwargs)
        else:
            task(self, *args, **kwargs)
