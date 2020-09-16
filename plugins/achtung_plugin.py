from global_variables import TELEGRAM_BOT


def achtung(message):
    addressee = [user_id for user_id, user_info in TELEGRAM_BOT.value.get_users().items() if not user_info['is_bot']]
    text = message.text.replace('/achtung', '_Общее сообщение!_\n\n')
    for telegram_id in addressee:
        TELEGRAM_BOT.value.send_message(telegram_id, text, parse_mode='Markdown')
