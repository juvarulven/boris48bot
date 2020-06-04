"""
Плагин тестирования
"""
from bot_admin import ADMIN_ID


def test_simple(bot, message):
    print('test_simple work')
    bot.send_message(message.from_user.id, 'passed!')


def test_scheduled():
    print('sending scheduled test message')
    return {'task': 'send_text', 'id': [ADMIN_ID], 'message': 'scheduled test passed!'}


__all__ = ['test_simple', 'test_scheduled']