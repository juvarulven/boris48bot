"""
Плагин тестирования
"""
from config import BOT_OWNER_ID


def test_simple(bot, message):
    print('test_simple work')
    print(message)
    bot.send_message(message.from_user.id, 'passed!')


def test_scheduled(bot):
    print('sending scheduled test message')
    bot.send_message(BOT_OWNER_ID, 'Scheduled test work')


__all__ = ['test_simple', 'test_scheduled']