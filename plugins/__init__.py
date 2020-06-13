"""
Как добавлять плагины:

1* Создать модуль плагина в этой же папке, например my_plugin.py.

2* Создать в нем функцию-обработчик некоего события:

2.1* Если функция должена срабатывать по комманде из телеграмма (далее "command handler"),
она должна принимать 2 аргумента. Пример:

def my_command_plugin(bot, message):
    bot.send_message(message.from_user.id, 'какое-то сообщение')

bot: объект бота телеграма для взаимодействия с ним. Подробнее в документации на pyTelegramBotApi,
message: объект сообщения из телеграма, по которому вызван бот

2.2* Если функция должна срабатывать через определенные промежутки времени (далее scheduled handler),
она может возвращать словарь с заданием для диспетчера (задел на будущее. Задания пока не реализованы):
{'task': 'задание', 'some_arg_1': 'какой-то аргумент'...}

3* Импротировать плагин сюда. Пример:

from . import my_plugin

4* Зарегистрировать функции в специальных переменных здесь:

4.1* Для command handler'ов добавить в список command_handlers словарь вида:

{'commands': ['комманда'...], 'handler': плагин.функция-обработчик}

4.2* Для scheduled handler'oв добавить в список scheduled_handler словарь вида:

{'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}

5* Добавить в commands_list плагина help_plugins.py справку по комманде, если нужно.
"""

from . import test_plugin
from . import help_plugin
from . import speak_plugin
from . import vault_plugin
from . import stop_plugin

command_handlers = [{'commands': ['start'], 'handler': help_plugin.start_message},
                    {'commands': ['help'], 'handler': help_plugin.help_message},
                    {'commands': ['test'], 'handler': test_plugin.test_simple},
                    {'commands': ['speak'], 'handler': speak_plugin.speak_message},
                    {'commands': ['subflow'], 'handler': vault_plugin.vault.subscribe_flow},
                    {'commands': ['subboris'], 'handler': vault_plugin.vault.subscribe_boris},
                    {'commands': ['unsubflow'], 'handler': vault_plugin.vault.unsubscribe_flow},
                    {'commands': ['unsubboris'], 'handler': vault_plugin.vault.unsubscribe_boris},
                    {'commands': ['killall'], 'handler': stop_plugin.stop}] # TODO сделать access level'ы

scheduled_handlers = [{'handler': vault_plugin.vault.scheduled, 'minutes': 1}]

__all__ = ['command_handlers', 'scheduled_handlers']
