"""
Модуль диспетчера с классом Dispatcher -- загружает плагины и рулит планировщиком
"""
from typing import Optional, List
from threading import Thread
from datetime import datetime, timedelta
from globalobjects import RUNNING_FLAG
import time
import log


class Dispatcher(Thread):
    def __init__(self, bot, plugins: List[dict], scheduled_plugins: Optional[List[dict]] = None):
        """
        Класс работает в отдельном треде
        Методы:
        run -- запускает тред
        scheduler -- запускает всякие обработчики в определенные промежутки времени
        task_handler -- пока не делает ничего. Задел на будущее
        :param bot: объект телеграм-бота, чтобы взаимодействовать с ним
        :param plugins: список словарей командных плагинов вида
        {'commands': ['комманда'...], 'handler': плагин.функция-обработчик}
        :param scheduled_plugins: список словарей периодичных плагинов вида
        {'handler': плагин.функция, 'minutes': периодичность срабатывания в минутах типа float или int}
        """
        super().__init__(daemon=True)
        self.__plugins = plugins
        self.__scheduled_plugins = scheduled_plugins
        self.__bot = bot
        self.__tasks_stack = []

    def run(self) -> None:
        """
        Запихивает список обработчиков комманд в объект бота, а потом запускает
        бесконечный цикл который дергает периодичные плагины
        Он будет крутиться, пока RUNNING_FLAG() не вернет false Подробнее в модуле globalobjects
        :return: None
        """
        if self.__scheduled_plugins is None:
            self.__scheduled_plugins = []
        self.__bot.load_command_plugins(self.__plugins)
        log.log('=== bot started ===')
        while RUNNING_FLAG():
            self.scheduler()
            while self.__tasks_stack:
                task = self.__tasks_stack.pop()
                self.task_handler(**task)
            time.sleep(1)
        self.__bot.stop_polling()
        log.log('=== bot stopped ===')

    def scheduler(self) -> None:
        """
        Запускает переодичные плагины в определенные промежутки времени
        :return: None
        """
        dt = datetime.utcnow()
        for plugin in self.__scheduled_plugins:
            if 'next_time' not in plugin:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
            if plugin['next_time'] < dt:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
                task = plugin['handler'](self.__bot)
                if task:
                    self.__tasks_stack.append(task)

    def task_handler(self, **kwargs):
        pass
