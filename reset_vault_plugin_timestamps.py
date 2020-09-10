import pprint
from datetime import datetime

import bson

VAULT_PLUGIN_FILEPATH = 'res/bsons/vault_plugin.bson'
USERS_FILEPATH = 'res/bsons/users.bson'


def open_file(filepath: str) -> dict:
    with open(filepath, 'rb') as file:
        db = bson.loads(file.read())
    return db


def save_file(filepath: str, db: dict) -> None:
    db = bson.dumps(db)
    with open(filepath, 'wb') as file:
        file.write(db)


def reset_timestamps(db: dict) -> None:
    timestamp = datetime.utcnow().isoformat(timespec='milliseconds')[:-1] + 'Z'
    db['last_updates']['boris']['timestamp'] = timestamp
    db['last_updates']['flow']['timestamp'] = timestamp
    for node_id in db['last_updates']['comments']:
        db['last_updates']['comments'][node_id]['timestamp'] = timestamp


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    db = open_file(VAULT_PLUGIN_FILEPATH)
    print('=======BEFORE=======')
    pp.pprint(db)
    reset_timestamps(db)
    print('\n=======AFTER=======')
    pp.pprint(db)
    save_file(VAULT_PLUGIN_FILEPATH, db)

