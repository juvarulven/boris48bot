from dispatcher import Dispatcher
from telegram import Bot
from plugins import command_handlers, scheduled_handlers
from config import TOKEN

bot = Bot(TOKEN)
dp = Dispatcher(bot, command_handlers, scheduled_plugins=scheduled_handlers)

if __name__ == "__main__":
    dp.start()
    bot.polling(none_stop=True)
