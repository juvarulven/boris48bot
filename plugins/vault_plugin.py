import sqlite3
import requests
import datetime
from config import DATABASE


class Vault:
    def __init__(self, vault_url, api_port, database):
        self.vault_url = vault_url
        self.api_port = api_port
        self.flow_api_url = '{}:{}/node/diff'.format(vault_url, api_port)
        self.boris_api_url = '{}:{}/node/696/comment'.format(vault_url, api_port)
        self.flow_messages = []
        self.boris_messages = []
        self.subscribers = {'flow': [], 'boris': []}
        self.database = database
        self.flow_last_update = None
        self.boris_last_update = None
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS vault_last_update (flow TEXT, boris INTEGER)')
        if cursor.execute('SELECT * FROM vault_last_update').fetchone() is None:
            self.flow_last_update = datetime.datetime.utcnow().isoformat(sep='T', timespec='milliseconds') + 'Z'
            params = {'take': 1,
                      'skip': 0}
            status = 0
            response = None
            while status != 200:
                response = requests.get(self.boris_api_url, params=params)
                status = response.status_code
            response = response.json()['comments'][0]
            self.boris_last_update = response['id']
            cursor.execute('INSERT INTO vault_last_update VALUES("{}", {})'.format(self.flow_last_update,
                                                                                   self.boris_last_update))
        else:
            last_updates = cursor.execute('SELECT * FROM vault_last_update').fetchone()
            self.flow_last_update, self.boris_last_update = last_updates
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
        cursor.execute('UPDATE vault_last_update SET {0} = {1} WHERE {0}'.format(column, last_update))
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

    def update_flow(self):
        params = {'start': self.flow_last_update,
                  'end': self.flow_last_update,
                  'with_heroes': False,
                  'with_updated': False,
                  'with_recent': False,
                  'with_valid': False}
        status = 0
        response = None
        while status != 200:
            response = requests.get(self.flow_api_url, params=params)
            status = response.status_code
        response = response.json()['before']
        while response:
            message = response.pop()
            self.flow_messages.append(message)
        if self.flow_messages:
            self.flow_last_update = datetime.datetime.utcnow().isoformat(timespec='milliseconds')
            self.update_database('flow', self.flow_last_update)

    def update_boris(self):
        params = {'take': 25,
                  'skip': 0}
        status = 0
        response = None
        while status != 200:
            response = requests.get(self.boris_api_url, params=params)
            status = response.status_code
        response = response.json()['comments']
        response.reverse()
        comment = response.pop()
        while comment['id'] > self.boris_last_update:
            self.boris_messages.append(comment)
            comment = response.pop()
        if self.boris_messages:
            self.boris_last_update = self.boris_messages[0]['id']
            self.update_database('boris', self.boris_last_update)

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

    def create_image_task(self, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился фото в Течении:' \
                   '\n\n*{}*и написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        return {'task': 'send_md_text', 'id': self.subscribers['flow'], 'message': message}

    def create_text_task(self, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился мыслями в Течении:' \
                   '\n\n*{}*\n{}\n{}'
        message = template.format(author, title, description, link)
        return {'task': 'send_md_text', 'id': self.subscribers['flow'], 'message': message}

    def create_audio_task(self, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился аудиозаписью в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        return {'task': 'send_md_text', 'id': self.subscribers['flow'], 'message': message}

    def create_video_task(self, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился видеозаписью в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        return {'task': 'send_md_text', 'id': self.subscribers['flow'], 'message': message}

    def create_other_task(self, author, title, description, link):
        template = 'Скрывающийся под псевдонимом _~{}_ поделился чем-то неординарным в Течении:' \
                   '\n\n*{}*\nи написал:\n{}\n{}'
        message = template.format(author, title, description, link)
        return {'task': 'send_md_text', 'id': self.subscribers['flow'], 'message': message}

    def create_boris_task(self, author, comment):
        template = 'Скрывающийся под псевдонимом _~{}_ вот что пишет Борису:' \
                   '\n\n{}\n{}'
        link = 'https://vault48.org/boris'
        message = template.format(author, comment, link)
        return {'task': 'send_md_text', 'id': self.subscribers['boris'], 'message': message}

    def scheduled(self):
        tasks = []
        self.update_flow()
        self.update_boris()
        while self.flow_messages:
            post = self.flow_messages.pop()
            author = post['user']['username']
            title = post['title']
            description = post['description']
            link = 'https://{}/post{}'.format(self.vault_url, post['id'])
            content_type = post['type']
            if content_type == 'image':
                tasks.append(self.create_image_task(author, title, description, link))
            if content_type == 'text':
                tasks.append(self.create_text_task(author, title, description, link))
            if content_type == 'audio':
                tasks.append(self.create_audio_task(author, title, description, link))
            if content_type == 'video':
                tasks.append(self.create_video_task(author, title, description, link))
            if content_type == 'other':
                tasks.append(self.create_other_task(author, title,description, link))
        while self.boris_messages:
            comment = self.boris_messages.pop()
            author = comment['user']['username']
            text = comment['text']
            tasks.append(self.create_boris_task(author, text))
        return tasks


VAULT_URL = 'https://vault48.org'
VAULT_PORT = 3333

vault = Vault(VAULT_URL, VAULT_PORT, DATABASE)

__all__ = ['vault']
