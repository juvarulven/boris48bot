"""
Как добавлять плагины:
1. Создать модуль плагина в этой же папке, например my_plugin.py.

2. Создать в нем функцию-обработчик некоего события:
2.1 Если функция должена срабатывать по комманде из телеграмма (далее "command handler"),
она должна принимать 2 аргумента. Пример:

def my_command_plugin(bot, message):
    bot.send_message(message.from_user.id, 'какое-то сообщение')

bot: объект бота телеграма для взаимодействия с ним. Подробнее в документации на pyTelegramBotApi,
message: объект сообщения из телеграма, по которому вызван бот

2.2 Если функция должна срабатывать через определенные промежутки времени (далее scheduled handler),
она может возвращать словарь с заданием для диспетчера. Пример:

def my_scheduled_plugin():
    return {'task': 'send_text', 'id': ['123456789'], 'message': 'какое-то сообщение'}

3. Импротировать плагин сюда. Пример:

from . import my_plugin

4. Зарегистрировать функции в специальных переменных здесь:
4.1 Для command handler'ов добавить в список command_handlers словарь вида:

{'commands': ['комманда'...], 'handler': плагин.функция-обработчик, 'help': 'краткое описание для команд справки'}

4.2 Для scheduled handler'oв добавить в список scheduled_handler словарь вида:

{'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}
"""

from . import test_plugin
from . import help_plugin

command_handlers = [{'commands': ['start'], 'handler': help_plugin.start_message, 'help': 'присылаю приветствие'},
                    {'commands': ['help'], 'handler': help_plugin.help_message, 'help': 'присылаю справку по командам'},
                    {'commands': ['test'], 'handler': test_plugin.test_simple, 'help': 'отвечаю "passed!"'}]

scheduled_handlers = [{'handler': test_plugin.test_scheduled, 'minutes': 1}]

__all__ = ['command_handlers', 'scheduled_handlers']
