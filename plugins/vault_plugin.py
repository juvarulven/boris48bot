import database as db
import requests
import log
from config import VAULT_URL, VAULT_API_PORT
from global_variables import RUNNING_FLAG
from vault_api import Api


class Vault:
    def __init__(self, vault_url, api_port):
        self._api = Api(vault_url, api_port)
        self._flow_messages = []
        self._boris_messages = []
        self._subscribers = {'flow': [], 'boris': []}
        self._db_timestamps_table = 'vault_timestamps'
        self._init_database()

    def _init_database(self):
        db.create_table(self._db_timestamps_table)
        last_updates = db.select(self._db_timestamps_table)
        if not last_updates:
            timestamps_and_comments_count = {}
            counter = 5
            while not timestamps_and_comments_count and counter:
                for name, value in self._api.get_comments_count_and_timestamps():
                    timestamps_and_comments_count[name] = value
                counter -= 1
            if timestamps_and_comments_count:
                pass  # TODO: доделать
            else:
                log.log('vault_plugin: Не удалось получить timestamp\'ы Убежища пять раз')
                RUNNING_FLAG.value = False
        else:
            _, self._flow_timestamp, self._boris_timestamp, self._comments_count = last_updates[0]
        db.add_column('users', 'vault_flow_subscriber', default=0)
        db.add_column('users', 'vault_boris_subscriber', default=0)
        raw_subscribers = db.select('users', 'id', condition='vault_flow_subscriber = 1')
        self._subscribers['flow'] = list(map(lambda x: x[0], raw_subscribers))
        raw_subscribers = db.select('users', 'id', condition='vault_boris_subscriber = 1')
        self._subscribers['boris'] = list(map(lambda x: x[0], raw_subscribers))

    def _add_subscriber(self, target, telegram_id):
        if telegram_id not in self._subscribers[target]:
            self._subscribers[target].append(telegram_id)
            condition = 'id = {}'.format(telegram_id)
            if target == 'flow':
                db.update('users', condition, vault_flow_subscriber=1)
            elif target == 'boris':
                db.update('users', condition, vault_boris_subscriber=1)
            else:
                raise AssertionError('target может быть либо "flow", либо "boris"')
            return True
        else:
            return False

    def _delete_subscriber(self, target, telegram_id):
        if telegram_id in self._subscribers[target]:
            self._subscribers[target].remove(telegram_id)
            condition = 'id = {}'.format(telegram_id)
            if target == 'flow':
                db.update('users', condition, vault_flow_subscriber=0)
            elif target == 'boris':
                db.update('users', condition, vault_boris_subscriber=0)
            else:
                raise AssertionError('target может быть либо "flow", либо "boris"')
            return True
        else:
            return False

    def _check_updates(self):
        status = 0
        response = None
        try:
            response = requests.get(self._stats_api_url)
            status = response.status_code
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при проверке обновлений Убежища: ' + str(error)
            log.log(error_message)
        if status != 200:
            return

        response = response.json()
        flow_timestamp = response['timestamps']['flow_last_post']
        boris_timestamp = response['timestamps']['boris_last_comment']
        comments_count = response['comments']['total']
        if flow_timestamp > self._flow_timestamp:
            self._update_flow(flow_timestamp)
        if boris_timestamp > self._boris_timestamp:
            self._update_boris(boris_timestamp, comments_count)

    def _update_flow(self, timestamp):
        params = {'start': self._flow_timestamp,
                  'end': self._flow_timestamp,
                  'with_heroes': False,
                  'with_updated': False,
                  'with_recent': False,
                  'with_valid': False}

        status = 0
        response = None
        try:
            response = requests.get(self._flow_api_url, params=params)
            status = response.status_code
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при проверке обновлений Течения: ' + str(error)
            log.log(error_message)
        if status != 200:
            return

        self._flow_timestamp = timestamp
        self._flow_messages = response.json()['before']
        db.update(self._db_timestamps_table, 'id = 0', flow_timestamp=timestamp)

    def _update_boris(self, timestamp, comments_count):
        params = {'take': comments_count - self._comments_count + 10,
                  'skip': 0}

        status = 0
        response = None
        try:
            response = requests.get(self._boris_api_url, params=params)
            status = response.status_code
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при проверке обновлений Бориса: ' + str(error)
            log.log(error_message)
        if status != 200:
            return

        response = response.json()['comments']
        for comment in response:
            if comment['created_at'] > self._boris_timestamp:
                self._boris_messages.append(comment)
            else:
                break
        self._boris_timestamp = timestamp
        self._comments_count = comments_count
        db.update(self._db_timestamps_table, 'id = 0', boris_timestamp=timestamp, comments_count=comments_count)

    def subscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._add_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Течение')

    def subscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._add_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Бориса')

    def unsubscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._delete_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Течение')

    def unsubscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._delete_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Бориса')

    def _send_image_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился фото в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_text_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился мыслями в Течении:_' \
                   '\n*{}*\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_audio_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился аудиозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_video_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился видеозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_other_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился чем-то неординарным в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_boris_message(self, bot, author, comment, with_files):
        template = '_Скрывающийся под псевдонимом_ *~{}* _вот что пишет Борису:_' \
                   '\n{}{}\n{}'
        link = 'https://vault48.org/boris'
        if with_files:
            with_files = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        else:
            with_files = ''
        message = template.format(author, comment, with_files, link)
        for addressee in self._subscribers['boris']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def scheduled(self, bot):
        self._check_updates()
        while self._flow_messages:
            post = self._flow_messages.pop()
            author = post['user']['username']
            title = post['title']
            description = post['description']
            link = 'https://{}/post{}'.format(self._vault_url, post['id'])
            content_type = post['type']
            if content_type == 'image':
                self._send_image_message(bot, author, title, description, link)
            if content_type == 'text':
                self._send_text_message(bot, author, title, description, link)
            if content_type == 'audio':
                self._send_audio_message(bot, author, title, description, link)
            if content_type == 'video':
                self._send_video_message(bot, author, title, description, link)
            if content_type == 'other':
                self._send_other_message(bot, author, title, description, link)
        while self._boris_messages:
            with_files = False
            comment = self._boris_messages.pop()
            author = comment['user']['username']
            text = comment['text']
            if comment['files']:
                with_files = True
            while self._boris_messages and self._boris_messages[-1]['user']['username'] == author:
                comment = self._boris_messages.pop()
                text += '\n_и продолжает:_\n'
                text += comment['text']
                if comment['files']:
                    with_files = True
            self._send_boris_message(bot, author, text, with_files)


vault = Vault(VAULT_URL, VAULT_API_PORT)

__all__ = ['vault']
