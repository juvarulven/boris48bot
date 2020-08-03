"""
Плагин тестирования
"""
from config import BOT_OWNER_ID
from global_variables import TELEGRAM_BOT


def test_simple(message):
    print('test_simple work')
    print(message)
    TELEGRAM_BOT.value.send_message(message.from_user.id, 'passed!')


def test_scheduled():
    print('sending scheduled test message')
    TELEGRAM_BOT.value.send_message(BOT_OWNER_ID, 'Scheduled test work')


__all__ = ['test_simple', 'test_scheduled']
