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

{'commands': ['комманда'...], 'handler': плагин.функция-обработчик, 'access_level': уровень доступа}

Уровни доступа 1 присваиваются пользователям, когда они пишут боту в первый раз.
Уровень доступа 2 присваиватся пользователю, ID которого указан в BOT_OWNER_ID модуля config.py
Уровень доступа 0 присваивается всем ботам, которые пишут этому боту.

5.2* Для scheduled handler'oв добавить в список scheduled_handler словарь вида:

{'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}

6* Добавить в commands_list плагина help_plugins.py справку по комманде, если нужно.

Если плагин должен уметь останавливать бота, нужно импортировать в него RUNNING_FLAG из global_variables.
RUNNING_FLAG.value = False штатно остановит бота
"""
from typing import Dict, List, Callable, Any, Union

from . import test_plugin
from . import help_plugin
from . import speak_plugin
from . import vault_plugin
from . import stop_plugin
from . import who_plugin

command_handlers: List[Dict[str, Union[List[str], Callable[[Any], None], int]]] = [
    {'commands': ['start'], 'handler': help_plugin.start_message, 'access_level': 1},
    {'commands': ['help'], 'handler': help_plugin.help_message, 'access_level': 1},
    {'commands': ['test'], 'handler': test_plugin.test_simple, 'access_level': 1},
    {'commands': ['speak'], 'handler': speak_plugin.speak_message, 'access_level': 1},
    {'commands': ['sub'], 'handler': vault_plugin.vault.sub, 'access_level': 1},
    {'commands': ['unsub'], 'handler': vault_plugin.vault.unsub, 'access_level': 1},
    {'commands': ['who'], 'handler': who_plugin.who, 'access_level': 2},
    {'commands': ['stop'], 'handler': stop_plugin.stop, 'access_level': 2}
]

scheduled_handlers: List[Dict[str, Union[Callable[[None], None]], int, float]] = [
    {'handler': vault_plugin.vault.scheduled, 'minutes': 1}
]

__all__ = ['command_handlers', 'scheduled_handlers']
