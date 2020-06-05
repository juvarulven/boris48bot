import sqlite3
import requests
import json
import datetime


class Vault:
    def __init__(self, vault_url, api_port, database):
        self.vault_url = vault_url
        self.api_port = api_port
        self.flow_messages = []
        self.boris_messages = []
        self.flow_subscribers = []
        self.boris_subscribers = []
        self.database = database

    def create_database(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE vault_last_update_time (flow text, boris text)')

