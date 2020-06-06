import sqlite3
import requests
import json
import datetime


class Vault:
    def __init__(self, vault_url, api_port, database):
        self.vault_url = vault_url
        self.api_port = api_port
        self.flow_api_url = 'https://{}:{}/node/diff'.format(vault_url, api_port)
        self.boris_api_url = 'https://{}:{}/node/696/comment'.format(vault_url, api_port)
        self.flow_messages = []
        self.boris_messages = []
        self.flow_subscribers = []
        self.boris_subscribers = []
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
                response = requests.get(self.boris_api_url, params)
                status = response.status_code
            response = json.loads(response.text)
            self.boris_last_update = response[0]['id']
            cursor.execute('INSERT INTO vault_last_update VALUES("{}", {})'.format(self.flow_last_update,
                                                                                   self.boris_last_update))
            conn.commit()
        else:
            last_updates = cursor.execute('SELECT * FROM vault_last_update').fetchone()
            self.flow_last_update, self.boris_last_update = last_updates

    def update_database(self, column, last_update):
        if isinstance(last_update, str):
            last_update = '"{}"'.format(last_update)
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute('UPDATE vault_last_update SET {0} = {1} WHERE {0}'.format(column, last_update))
        conn.commit()

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
            response = requests.get(self.flow_api_url, params)
            status = response.status_code
        response = json.loads(response.text)
        self.flow_messages = response['before']
        if self.flow_messages:
            dt = datetime.datetime.utcnow().isoformat(timespec='milliseconds')
            self.update_database('flow', dt)

    def update_boris(self):
        params = {'take': 25,
                  'skip': 0}
        status = 0
        response = None
        while status != 200:
            response = requests.get(self.boris_api_url, params)
            status = response.status_code
        response = json.loads(response.text)
        response = response['comments']
        slice_border = 0
        for slice_border, comment in enumerate(response):
            if comment['id'] == self.boris_last_update:
                break
        if slice_border:
            self.boris_messages = response[:slice_border]
            self.update_database('boris', self.boris_messages[0]['id'])
