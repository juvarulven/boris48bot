"""
Плагин тестирования
"""
from config import ADMIN_ID


def test_simple(bot, message):
    print('test_simple work')
    bot.send_message(message.from_user.id, 'passed!')


def test_scheduled(bot):
    print('sending scheduled test message')
    bot.send_message(ADMIN_ID, 'Scheduled test work')


__all__ = ['test_simple', 'test_scheduled']