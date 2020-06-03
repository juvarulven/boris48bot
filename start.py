from dispatcher import Dispatcher
from telegram import Bot
from plugins import plugins, scheduled_plugins
from bot_token import TOKEN

bot = Bot(TOKEN)
dp = Dispatcher(bot, plugins, scheduled_plugins=scheduled_plugins)

if __name__ == "__main__":
    dp.start()
    bot.polling(none_stop=True)
