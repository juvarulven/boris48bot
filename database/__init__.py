import bson
import os.path


class Database:
    file_lock = False

    def __init__(self, filename):
        self._filename = filename
        self.db = None

    def load(self, filename=None):
        if filename is None:
            filename = self._filename
        if os.path.exists(filename):
            with open(filename, 'rb') as db:
                self.db = bson.loads(db.read())
        else:
            with open(filename, 'wb') as db:
                db.write(bson.dumps({}))



