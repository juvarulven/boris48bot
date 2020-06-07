"""
Плагин реакции на команды /start и /help

commands_list -- список строк команд с описанием
"""

commands_list = ['/start: отправлять приветствие',
                 '/help: присылать краткую справка по командам',
                 '/test: отвечать "passed!"',
                 '/speak: говорить фразу, украденную из Убежища',
                 '/subflow, /subboris: подписывать на обновления Течения и Бориса',
                 '/unsubflow, /unsubboris: отписывать от обновлений Течения и Бориса']

commands = '\n'.join(commands_list)


def start_message(bot, message):
    answer = 'Приветствую.\nЯ -- маленький бот сайта https://vault48.org\n\nВот что я умею:\n'
    answer += commands
    bot.send_message(message.from_user.id, answer)


def help_message(bot, message):
    answer = 'Вот что я умею:\n'
    answer += commands
    bot.send_message(message.from_user.id, answer)


__all__ = ['start_message', 'help_message']
