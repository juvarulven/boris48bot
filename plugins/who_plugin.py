"""
Отправляет список всех пользователей, которых знает бот
"""
from global_variables import TELEGRAM_BOT


def who(message):
    answer = "Вот кого я знаю:\n"
    users = TELEGRAM_BOT.value.get_users()
    for user_id, user_info in users.items():
        answer += 'робот:   ' if user_info['is_bot'] else 'человек: '
        answer += str(user_info['access_level']) + ' '
        answer += user_id + ' '
        answer += user_info['first_name'] + ' ('
        answer += user_info['username'] + ') '
        answer += user_info['last_name'] + '\n'
    TELEGRAM_BOT.value.send_message(message.from_user.id, answer)


__all__ = ['who']
