import database as db
import requests
from config import VAULT_URL, VAULT_API_PORT


class Vault:
    def __init__(self, vault_url, api_port):
        self.vault_url = vault_url
        self.api_port = api_port
        self.stats_api_url = '{}:{}/stats'.format(vault_url, api_port)
        self.flow_api_url = '{}:{}/node/diff'.format(vault_url, api_port)
        self.boris_api_url = '{}:{}/node/696/comment'.format(vault_url, api_port)
        self.flow_messages = []
        self.boris_messages = []
        self.subscribers = {'flow': [], 'boris': []}
        self.database_updates_table = 'vault_last_updates'
        self.flow_timestamp = None
        self.boris_timestamp = None
        self.comments_count = None

        self.__init_database()

    def __init_database(self):
        db.create_table(self.database_updates_table, flow_timestamp='', boris_timestamp='', comments_count=0)
        last_updates = db.select(self.database_updates_table)
        if not last_updates:
            status = 0
            response = None
            while status != 200:
                response = requests.get(self.stats_api_url)
                status = response.status_code
            response = response.json()
            self.flow_timestamp = response['timestamps']['flow_last_post']
            self.boris_timestamp = response['timestamps']['boris_last_comment']
            self.comments_count = response['comments']['total']
            db.insert(self.database_updates_table, 0, flow_timestamp=self.flow_messages,
                      boris_timestamp=self.boris_timestamp, comments_count=self.comments_count)
        else:
            self.flow_timestamp, self.boris_timestamp, self.comments_count = last_updates[0]
        db.add_column('users', 'vault_flow_subscriber')
        db.add_column('users', 'vault_boris_subscriber')
        raw_subscribers = db.select('users', 'id', condition='vault_flow_subscriber = 1')
        self.subscribers['flow'] = list(map(lambda x: x[0], raw_subscribers))
        raw_subscribers = db.select('users', 'id', condition='vault_boris_subscriber = 1')
        self.subscribers['boris'] = list(map(lambda x: x[0], raw_subscribers))

    def __add_subscriber(self, target, telegram_id):
        if telegram_id not in self.subscribers[target]:
            self.subscribers[target].append(telegram_id)
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

    def __delete_subscriber(self, target, telegram_id):
        if telegram_id in self.subscribers[target]:
            self.subscribers[target].remove(telegram_id)
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

    def __check_updates(self):
        response = requests.get(self.stats_api_url)
        if response.status_code != 200:
            return
        response = response.json()
        flow_timestamp = response['timestamps']['flow_last_post']
        boris_timestamp = response['timestamps']['boris_last_comment']
        comments_count = response['comments']['total']
        if flow_timestamp > self.flow_timestamp:
            self.__update_flow(flow_timestamp)
        if boris_timestamp > self.boris_timestamp:
            self.__update_boris(boris_timestamp, comments_count)

    def __update_flow(self, timestamp):
        params = {'start': self.flow_timestamp,
                  'end': self.flow_timestamp,
                  'with_heroes': False,
                  'with_updated': False,
                  'with_recent': False,
                  'with_valid': False}
        response = requests.get(self.flow_api_url, params=params)
        if response.status_code != 200:
            return
        self.flow_timestamp = timestamp
        self.flow_messages = response.json()['before']
        db.update(self.database_updates_table, 'id = 0', flow_timestamp=timestamp)

    def __update_boris(self, timestamp, comments_count):
        params = {'take': comments_count - self.comments_count + 10,
                  'skip': 0}
        response = requests.get(self.boris_api_url, params=params)
        if response.status_code != 200:
            return
        response = response.json()['comments']
        for comment in response:
            if comment['created_at'] > self.boris_timestamp:
                self.boris_messages.append(comment)
            else:
                break
        self.boris_timestamp = timestamp
        self.comments_count = comments_count
        db.update(self.database_updates_table, 'id = 0', boris_timestamp=timestamp, comments_count=comments_count)

    def subscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.__add_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Течение')

    def subscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.__add_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Бориса')

    def unsubscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.__delete_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Течение')

    def unsubscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.__delete_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Бориса')

    def __send_image_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился фото в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def __send_text_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился мыслями в Течении:_' \
                   '\n*{}*\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def __send_audio_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился аудиозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def __send_video_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился видеозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def __send_other_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился чем-то неординарным в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def __send_boris_message(self, bot, author, comment, with_files):
        template = '_Скрывающийся под псевдонимом_ *~{}* _вот что пишет Борису:_' \
                   '\n{}{}\n{}'
        link = 'https://vault48.org/boris'
        if with_files:
            with_files = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        else:
            with_files = ''
        message = template.format(author, comment, with_files, link)
        for addressee in self.subscribers['boris']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def scheduled(self, bot):
        self.__check_updates()
        while self.flow_messages:
            post = self.flow_messages.pop()
            author = post['user']['username']
            title = post['title']
            description = post['description']
            link = 'https://{}/post{}'.format(self.vault_url, post['id'])
            content_type = post['type']
            if content_type == 'image':
                self.__send_image_message(bot, author, title, description, link)
            if content_type == 'text':
                self.__send_text_message(bot, author, title, description, link)
            if content_type == 'audio':
                self.__send_audio_message(bot, author, title, description, link)
            if content_type == 'video':
                self.__send_video_message(bot, author, title, description, link)
            if content_type == 'other':
                self.__send_other_message(bot, author, title, description, link)
        while self.boris_messages:
            with_files = False
            comment = self.boris_messages.pop()
            author = comment['user']['username']
            text = comment['text']
            if comment['files']:
                with_files = True
            while self.boris_messages and self.boris_messages[-1]['user']['username'] == author:
                comment = self.boris_messages.pop()
                text += '\n_и продолжает:_\n'
                text += comment['text']
                if comment['files']:
                    with_files = True
            self.__send_boris_message(bot, author, text, with_files)


vault = Vault(VAULT_URL, VAULT_API_PORT)

__all__ = ['vault']
