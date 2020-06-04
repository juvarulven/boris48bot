from . import command_handlers

commands = ''
for plugin in command_handlers:
    commands += '\n'
    for command in plugin['commands']:
        commands += '/' + command + ' '
    commands += plugin['help']


def start_message(bot, message):
    answer = 'Приветствую. Я -- маленький бот сайта https://vault48.org\nВот что я умею:'
    answer += commands
    bot.send_message(message.from_user.id, answer)


def help_message(bot, message):
    answer = 'Вот что я умею:'
    answer += commands
    bot.send_message(message.from_user.id, answer)


__all__ = ['start_message', 'help_message']
