"""
Плагин реакции на команды /start и /help

commands_list -- список кортежей вида ('/команда: описание', уровень доступа)
"""
from global_variables import TELEGRAM_BOT

commands_list = [('/start: отправлять приветствие', 1),
                 ('/help: присылать краткую справку по командам', 1),
                 ('/test: отвечать "passed!"', 1),
                 ('/speak: говорить фразу, украденную из Убежища', 1),
                 ('/sub: подписывать на всякое новое в Убежище', 1),
                 ('/unsub: отписывать от всякого в Убежище', 1),
                 ('/stop: сушите весла!', 2)]


def _generate_message(message, header_text, footer_text=""):
    access_level = TELEGRAM_BOT.value.get_user_access_level(message.from_user.id)
    commands = [command[0] for command in filter(lambda item: item[1] >= access_level, commands_list)]
    return header_text + commands + footer_text


def start_message(message):
    answer = _generate_message(message,
                               'Приветствую.\nЯ -- маленький бот сайта https://vault48.org\n\nВот что я умею:\n')
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


def help_message(message):
    answer = _generate_message(message, 'Вот что я умею:\n')
    TELEGRAM_BOT.value.send_message(message.from_user_id, answer)


__all__ = ['start_message', 'help_message']
