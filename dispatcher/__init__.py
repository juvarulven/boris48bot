from threading import Thread
import datetime


class Dispatcher(Thread):
    def __init__(self, bot, plugins, scheduled_plugins=None):
        super().__init__(deamon=True)
        self.plugins = plugins
        self.scheduled_plugins = scheduled_plugins
        self.bot = bot
        self.running_flag = True

    def run(self):
        self.bot.load_command_plugins(self.plugins)
        self.bot.polling(none_stop=True)
        while self.running_flag:
            # todo: сделать полезную функциональность
            pass
