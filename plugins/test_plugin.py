def test_simple(bot, message):
    bot.send_message(message.from_user.id, 'passed!')


def test_scheduled():
    return {'task': 'send_text', 'id': [''], 'message': 'scheduled test passed!'}


__all__ = ['test_simple', 'test_scheduled']