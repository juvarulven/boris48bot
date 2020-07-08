"""
Плагин реакции на команды /start и /help

commands_list -- список строк команд с описанием
"""
from global_variables import TELEGRAM_BOT

commands_list = [('/start: отправлять приветствие', 1),
                 ('/help: присылать краткую справку по командам', 1),
                 ('/test: отвечать "passed!"', 1),
                 ('/speak: говорить фразу, украденную из Убежища', 1),
                 ('/sub: подписывать на всякое новое в Убежище', 1),
                 ('/unsub: отписывать от всякого в Убежище', 1)]


def _get_commands(access_level):
    commands = [command[0] for command in list(filter(lambda item: item[1] >= access_level))]
    return '\n'.join(commands)


def start_message(message):
    commands = _get_commands(TELEGRAM_BOT.value.get_user_access_level(message.from_user.id))
    answer = 'Приветствую.\nЯ -- маленький бот сайта https://vault48.org\n\nВот что я умею:\n'
    answer += commands
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


def help_message(message):
    commands = _get_commands(TELEGRAM_BOT.value.get_user_access_level(message.from_user.id))
    answer = 'Вот что я умею:\n'
    answer += commands
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


__all__ = ['start_message', 'help_message']
