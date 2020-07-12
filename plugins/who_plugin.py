"""
Отправляет список всех пользователей, которых знает бот
"""
from global_variables import TELEGRAM_BOT


def who(message):
    answer = "Вот кого я знаю:\n"
    row_template = '{} {} {} ({}) {} {}\n'
    users = TELEGRAM_BOT.value.get_users()
    for user_id, user_info in users.items():
        is_bot = 'робот:   ' if user_info['is_bot'] else 'человек: '
        access_level = user_info['access_level']
        first_name = user_info['first_name']
        first_name = first_name if first_name else '...'
        username = user_info['username']
        username = username if username else '...'
        last_name = user_info['last_name']
        last_name = last_name if last_name else '...'
        answer += row_template.format(user_id, is_bot, first_name, username, last_name, access_level)
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


__all__ = ['who']
