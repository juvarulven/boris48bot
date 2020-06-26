"""
Плагин реакции на команды /start и /help

commands_list -- список строк команд с описанием
"""
from global_variables import TELEGRAM_BOT

commands_list = ['/start: отправлять приветствие',
                 '/help: присылать краткую справку по командам',
                 '/test: отвечать "passed!"',
                 '/speak: говорить фразу, украденную из Убежища',
                 '/subflow, /subboris: подписывать на обновления Течения и Бориса',
                 '/unsubflow, /unsubboris: отписывать от обновлений Течения и Бориса']

commands = '\n'.join(commands_list)


def start_message(message):
    answer = 'Приветствую.\nЯ -- маленький бот сайта https://vault48.org\n\nВот что я умею:\n'
    answer += commands
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


def help_message(message):
    answer = 'Вот что я умею:\n'
    answer += commands
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


__all__ = ['start_message', 'help_message']
