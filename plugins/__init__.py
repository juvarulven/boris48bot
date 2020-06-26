"""
Как добавлять плагины:

1* Создать модуль плагина в этой же папке, например my_plugin.py.

2* Если надо, импортировать в нем TELEGRAM_BOT из global_variables (жуткий костыль для взаимодействия с ботом). То есть:

from global_variables import TELEGRAM_BOT

TELEGRAM_BOT.value возвращает инстанс бота

3* Создать в модуле функцию-обработчик некоего события:

3.1* Если функция должена срабатывать по комманде из телеграмма (далее "command handler"),
она должна принимать аргумент сообщения. Пример:

def my_command_plugin(message):
    TELEGRAM_BOT.value.send_message(message.from_user.id, 'какое-то сообщение')

3.2* Если функция должна срабатывать через определенные промежутки времени (далее scheduled handler),
она может возвращать словарь с заданием для диспетчера (задел на будущее. Задания пока не реализованы):
{'task': 'задание', 'some_arg_1': 'какой-то аргумент'...}

4* Импротировать плагин сюда. Пример:

from . import my_plugin

5* Зарегистрировать функции в специальных переменных здесь:

5.1* Для command handler'ов добавить в список command_handlers словарь вида:

{'commands': ['комманда'...], 'handler': плагин.функция-обработчик}

5.2* Для scheduled handler'oв добавить в список scheduled_handler словарь вида:

{'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}

6* Добавить в commands_list плагина help_plugins.py справку по комманде, если нужно.

Если плагин должен уметь останавливать бота, нужно импортировать в него RUNNING_FLAG из global_variables.
RUNNING_FLAG.value = False штатно остановит бота
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
                    {'commands': ['sub'], 'handler': vault_plugin.vault.sub},
                    {'commands': ['unsub'], 'handler': vault_plugin.vault.unsub},
                    {'commands': ['killall'], 'handler': stop_plugin.stop}]  # TODO сделать access level'ы

scheduled_handlers = [{'handler': vault_plugin.vault.scheduled, 'minutes': 1}]

__all__ = ['command_handlers', 'scheduled_handlers']
