"""
Модуль диспетчера с классом Dispatcher -- загружает плагины и рулит планировщиком
"""
from typing import Optional, List
from threading import Thread
from datetime import datetime, timedelta
from global_variables import RUNNING_FLAG
import time
import log


class Dispatcher(Thread):
    """
    Класс работает в отдельном треде
    Методы:
    run -- запускает тред
    _scheduler -- запускает всякие обработчики в определенные промежутки времени
    _task_handler -- пока не делает ничего. Задел на будущее
    """
    def __init__(self, bot, plugins: List[dict], scheduled_plugins: Optional[List[dict]] = None):
        """
        Принимает объект бота, и списки словарей плагинов

        :param bot: объект телеграм-бота, чтобы взаимодействовать с ним
        :param plugins: список словарей командных плагинов вида
        {'commands': ['комманда'...], 'handler': плагин.функция-обработчик}
        :param scheduled_plugins: список словарей периодичных плагинов вида
        {'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}
        """
        super().__init__(daemon=True)
        self._plugins = plugins
        self._scheduled_plugins = scheduled_plugins
        self._bot = bot
        self._tasks_stack = []

    def run(self) -> None:
        """
        Запихивает список обработчиков комманд в объект бота, а потом запускает
        бесконечный цикл который дергает периодичные плагины
        Он будет крутиться, пока RUNNING_FLAG() не вернет false Подробнее в модуле globalobjects

        :return: None
        """
        if self._scheduled_plugins is None:
            self._scheduled_plugins = []
        self._bot.load_command_plugins(self._plugins)
        log.log('=== bot started ===')
        while RUNNING_FLAG.value:
            self._scheduler()
            while self._tasks_stack:
                task = self._tasks_stack.pop()
                self._task_handler(**task)
            time.sleep(1)
        self._bot.stop_polling()
        log.log('=== bot stopped ===')

    def _scheduler(self) -> None:
        """
        Запускает переодичные плагины в определенные промежутки времени

        :return: None
        """
        dt = datetime.utcnow()
        for plugin in self._scheduled_plugins:
            if 'next_time' not in plugin:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
            if plugin['next_time'] < dt:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
                task = plugin['handler']()
                if task:
                    self._tasks_stack.append(task)

    def _task_handler(self, **kwargs):
        pass
