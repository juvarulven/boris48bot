from typing import Optional, Dict, Tuple
from database import Database
from vault_api import Api
import requests
import log
from datetime import datetime
from global_variables import RUNNING_FLAG


class Vault:
    def __init__(self):
        self._api = Api(testing=True)
        self._flow_messages = []
        self._boris_messages = []
        self._godnota_messages = []
        self._subscribers = {'flow': [], 'boris': [], 'comments': []}
        self._db_users = Database('users')
        self._db = Database('vault_plugin')
        self._last_updates = {'flow': {'timestamp': None, 'posts_count': None, 'subscribers': []},
                              'boris': {'timestamp': None, 'comments_count': None, 'subscribers': []},
                              'comments': {}, 'comments_count': None}
        self._godnota = None
        self._init_database()

    @staticmethod
    def _do_it_5_times(what_to_do, *args, **kwargs):
        response = None
        try_counter = 5
        while response is None and try_counter:
            response = what_to_do(*args, **kwargs)
            try_counter -= 1
        if response is None:
            RUNNING_FLAG.value = False
            log.log('vault_plugin: ошибка при попытке сделать {} 5 раз'.format(what_to_do.__name__))
            return
        return response

    def _init_database(self):
        need_update_db = False
        last_updates = self._db.get_document('last_updates')
        if last_updates is None:
            need_update_db = True
            stats = self._do_it_5_times(self._api.get_stats)
            # TODO: Сделать нормально, когда Григорий починит flow_last_post в API stats'ов
            now = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
            diff = self._do_it_5_times(self._api.get_diff, start=now, end=now)
            boris = self._do_it_5_times(self._api.get_boris, 1)
            if stats is None or diff is None or boris is None:
                log.log('vault_plugin: Не удалось получить stats, diff или boris за пять попыток')
                return
            self._last_updates['comments_count'] = stats.comments_total
            self._last_updates['flow']['timestamp'] = diff.after[0].created_at
            self._last_updates['flow']['posts_count'] = stats.nodes_total
            self._last_updates['boris']['timestamp'] = boris.comments[0].created_at
            self._last_updates['boris']['comments_count'] = boris.comment_count
        else:
            self._last_updates = last_updates
        self._godnota = self._do_it_5_times(self._api.get_godnota)
        if self._godnota is None:
            log.log('vault_plugin: Не удалось получить годноту за пять попыток')
            return
        for title, post_id in self._godnota:
            if post_id not in self._last_updates['comments']:
                need_update_db = True
                comments = self._do_it_5_times(self._api.get_comments, post_id, 1)
                if comments is None:
                    log.log('vault_plugin: не удалось получить комментарии из {} за пять попыток'.format(title))
                    return
                self._last_updates['comments'][post_id] = {}
                self._last_updates['comments'][post_id]['title'] = title
                self._last_updates['comments'][post_id]['timestamp'] = comments.comments[0].created_at
                self._last_updates['comments'][post_id]['comments_count'] = comments.comment_count
                self._last_updates['comments'][post_id]['subscribers'] = {}
        if need_update_db:
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()

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
        link = self._api.url + 'boris'
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
            link = '{}post{}'.format(self._api.url, post['id'])
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


vault = Vault()

__all__ = ['vault']
