from utils import log
from global_variables import RUNNING_FLAG, TELEGRAM_BOT


def stop(message):
    TELEGRAM_BOT.value.send_message(message.from_user.id, 'Останавливаюсь')
    log_message = 'Останавливаюсь по команде от @{}'.format(message.from_user.username)
    log.log(log_message)
    RUNNING_FLAG.value = False
