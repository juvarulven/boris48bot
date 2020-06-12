"""
Модуль диспетчера с классом Dispatcher -- загружает плагины и рулит планировщиком
"""
from typing import Optional, List
from telegram import Bot
from threading import Thread
from datetime import datetime, timedelta
import time


class Dispatcher(Thread):
    def __init__(self, bot: Bot, plugins: List[dict], scheduled_plugins: Optional[List[dict]] = None):
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
        self.__running_flag = True
        self.__tasks_stack = []

    def run(self) -> None:
        """
        Запихивает список обработчиков комманд в объект бота, а потом запускает
        бесконечный цикл диспетчера и все это в отдельном треде.
        Он будет крутиться, пока self.__running_flag не станет false (будет изменено)
        :return: None
        """
        if self.__scheduled_plugins is None:
            self.__scheduled_plugins = []
        self.__bot.load_command_plugins(self.__plugins)
        while self.__running_flag:  # TODO: сделать способ остановить бесконечный цикл по комманде извне
            self.scheduler()
            while self.__tasks_stack:
                task = self.__tasks_stack.pop()
                self.task_handler(**task)
            time.sleep(1)

    def scheduler(self) -> None:
        """
        Запускает переодичные плагины в определенные промежутки времени
        :return:
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
