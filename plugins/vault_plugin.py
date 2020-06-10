import sqlite3
import requests
from config import DATABASE


class Vault:
    def __init__(self, vault_url, api_port, database):
        self.vault_url = vault_url
        self.api_port = api_port
        self.stats_api_url = '{}:{}/stats'.format(vault_url, api_port)
        self.flow_api_url = '{}:{}/node/diff'.format(vault_url, api_port)
        self.boris_api_url = '{}:{}/node/696/comment'.format(vault_url, api_port)
        self.flow_messages = []
        self.boris_messages = []
        self.subscribers = {'flow': [], 'boris': []}
        self.database = database
        self.flow_timestamp = None
        self.boris_timestamp = None
        self.comments_count = None

        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        columns = ('flow_timestamp', 'boris_timestamp', 'comments_count')
        cursor.execute('CREATE TABLE IF NOT EXISTS vault_last_updates ({} TEXT, {} TEXT, {} INTEGER)'.format(*columns))
        last_updates = cursor.execute('SELECT * FROM vault_last_updates').fetchone()
        if last_updates is None:
            status = 0
            response = None
            while status != 200:
                response = requests.get(self.stats_api_url)
                status = response.status_code
            response = response.json()
            self.flow_timestamp = response['timestamps']['flow_last_post']
            self.boris_timestamp = response['timestamps']['boris_last_comment']
            self.comments_count = response['comments']['total']
            cursor.execute('INSERT INTO vault_last_updates VALUES("{}", "{}", {})'.format(self.flow_timestamp,
                                                                                          self.boris_timestamp,
                                                                                          self.comments_count))
        else:
            last_updates = cursor.execute('SELECT * FROM vault_last_updates').fetchone()
            self.flow_timestamp, self.boris_timestamp, self.comments_count = last_updates
        cursor.execute('CREATE TABLE IF NOT EXISTS flow_subscribers (id INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS boris_subscribers (id INTEGER)')
        conn.commit()
        raw_subscribers = cursor.execute('SELECT id FROM flow_subscribers').fetchall()
        self.subscribers['flow'] = list(map(lambda x: x[0], raw_subscribers))
        raw_subscribers = cursor.execute('SELECT id FROM boris_subscribers').fetchall()
        self.subscribers['boris'] = list(map(lambda x: x[0], raw_subscribers))

    def update_database(self, column, last_update):
        if isinstance(last_update, str):
            last_update = '"{}"'.format(last_update)
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute('UPDATE vault_last_updates SET {0} = {1} WHERE {0}'.format(column, last_update))
        conn.commit()

    def add_subscriber(self, target, telegram_id):
        if telegram_id not in self.subscribers[target]:
            self.subscribers[target].append(telegram_id)
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO {}_subscribers VALUES({})'.format(target, telegram_id))
            conn.commit()
            return True
        else:
            return False

    def delete_subscriber(self, target, telegram_id):
        if telegram_id in self.subscribers[target]:
            self.subscribers[target].remove(telegram_id)
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM {}_subscribers WHERE id={}'.format(target, telegram_id))
            conn.commit()
            return True
        else:
            return False

    def check_updates(self):
        response = requests.get(self.stats_api_url)
        if response.status_code != 200:
            return
        response = response.json()
        flow_timestamp = response['timestamps']['flow_last_post']
        boris_timestamp = response['timestamps']['boris_last_comment']
        comments_count = response['comments']['total']
        if flow_timestamp > self.flow_timestamp:
            self.update_flow(flow_timestamp)
        if boris_timestamp > self.boris_timestamp:
            self.update_boris(boris_timestamp, comments_count)

    def update_flow(self, timestamp):
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
        self.update_database('flow_timestamp', timestamp)

    def update_boris(self, timestamp, comments_count):
        params = {'take': comments_count - self.comments_count + 10,
                  'skip': 0}
        response = requests.get(self.boris_api_url, params=params)
        if response.status_code != 200:
            return
        response = response.json()['comments']
        for comment in response:
            if comment['created_at'] > timestamp:
                self.boris_messages.append(comment)
            else:
                break
        self.boris_timestamp = timestamp
        self.comments_count = comments_count
        self.update_database('boris_timestamp', timestamp)
        self.update_database('comments_count', comments_count)

    def subscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.add_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Течение')

    def subscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.add_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Бориса')

    def unsubscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.delete_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Течение')

    def unsubscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self.delete_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Бориса')

    def send_image_message(self, bot, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился фото в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def send_text_message(self, bot, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился мыслями в Течении:' \
                   '\n\n*{}*\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def send_audio_message(self, bot, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился аудиозаписью в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def send_video_message(self, bot, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился видеозаписью в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def send_other_message(self, bot, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился чем-то неординарным в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self.subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def send_boris_message(self, bot, author, comment):
        template = 'Скрывающийся под псевдонимом _~{}_ вот что пишет Борису:' \
                   '\n\n{}\n{}'
        link = 'https://vault48.org/boris'
        message = template.format(author, comment, link)
        for addressee in self.subscribers['boris']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def scheduled(self, bot):
        self.check_updates()
        while self.flow_messages:
            post = self.flow_messages.pop()
            author = post['user']['username']
            title = post['title']
            description = post['description']
            link = 'https://{}/post{}'.format(self.vault_url, post['id'])
            content_type = post['type']
            if content_type == 'image':
                self.send_image_message(bot, author, title, description, link)
            if content_type == 'text':
                self.send_text_message(bot, author, title, description, link)
            if content_type == 'audio':
                self.send_audio_message(bot, author, title, description, link)
            if content_type == 'video':
                self.send_video_message(bot, author, title, description, link)
            if content_type == 'other':
                self.send_other_message(bot, author, title, description, link)
        while self.boris_messages:
            comment = self.boris_messages.pop()
            author = comment['user']['username']
            text = comment['text']
            while self.boris_messages and self.boris_messages[-1]['user']['username'] == author:
                comment = self.boris_messages.pop()
                text += '\n++++++++++\n'
                text += comment['text']
            self.send_boris_message(bot, author, text)


VAULT_URL = 'https://vault48.org'
VAULT_PORT = 3333

vault = Vault(VAULT_URL, VAULT_PORT, DATABASE)

__all__ = ['vault']
