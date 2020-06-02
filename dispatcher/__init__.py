from threading import Thread
from datetime import datetime, timedelta


class Dispatcher(Thread):
    def __init__(self, bot, plugins, scheduled_plugins=None):
        super().__init__(deamon=True)
        self.plugins = plugins
        self.scheduled_plugins = scheduled_plugins
        self.bot = bot
        self.running_flag = True
        self.returns_stack = []

    def run(self):
        if self.scheduled_plugins is None:
            self.scheduled_plugins = []
        self.bot.load_command_plugins(self.plugins)
        self.bot.polling(none_stop=True)
        while self.running_flag:
            self.scheduler()
            while self.returns_stack:
                task = self.returns_stack.pop()
                self.task_handler(task)

    def scheduler(self):
        dt = datetime.utcnow()
        for plugin in self.scheduled_plugins:
            if 'next_time' not in plugin:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
            if plugin['next_time'] < dt:
                plugin['next_time'] = dt + timedelta(minutes=plugin['minutes'])
                self.returns_stack.append(plugin['handler']())

    def task_handler(self, task):
        if task['task'] == 'send_text':
            for telegram_id in task['id']:
                self.bot.send_message(telegram_id, task['message'])
