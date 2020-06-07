from threading import Thread
from datetime import datetime, timedelta
import time


class Dispatcher(Thread):
    def __init__(self, bot, plugins, scheduled_plugins=None):
        super().__init__(daemon=True)
        self.plugins = plugins
        self.scheduled_plugins = scheduled_plugins
        self.bot = bot
        self.running_flag = True
        self.tasks_stack = []

    def run(self):
        if self.scheduled_plugins is None:
            self.scheduled_plugins = []
        self.bot.load_command_plugins(self.plugins)
        while self.running_flag:
            self.scheduler()
            while self.tasks_stack:
                task = self.tasks_stack.pop()
                self.task_handler(task)
            time.sleep(1)

    def scheduler(self):
        dt = datetime.utcnow()
        for plugin in self.scheduled_plugins:
            if 'next_time' not in plugin:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
            if plugin['next_time'] < dt:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
                task_list = plugin['handler']()
                if isinstance(task_list, list):
                    while task_list:
                        task = task_list.pop()
                        self.tasks_stack.append(task)

    def task_handler(self, task):
        if task['task'] == 'send_text':
            for telegram_id in task['id']:
                self.bot.send_message(telegram_id, task['message'])
        if task['task'] == 'send_md_text':
            for telegram_id in task['id']:
                self.bot.send_message(telegram_id, task['message'], parse_mode='Markdown')
