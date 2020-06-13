import log
from globalobjects import RUNNING_FLAG


def stop(bot, message):
    bot.send_message(message.from_user.id, 'Останавливаюсь')
    log_message = 'Останавливаюсь по команде от @{}'.format(message.from_user.username)
    log.log(log_message)
    RUNNING_FLAG(False)
