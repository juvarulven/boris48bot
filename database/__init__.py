import bson
import os.path
import time


class Database:
    file_lock = {}

    def __init__(self, collection):
        self._filename = collection + '.bson'
        self.__class__.file_lock[self._filename] = False
        self.documents = {}

    def load(self):
        if os.path.exists(self._filename):
            with open(self._filename, 'rb') as table:
                self.documents = bson.loads(table.read())
        else:
            self.save()

    def save(self):
        while self.__class__.file_lock[self._filename]:
            time.sleep(0.01)
        self.__class__.file_lock[self._filename] = True
        with open(self._filename, 'wb') as table:
            table.write(bson.dumps(self.documents))
        self.__class__.file_lock[self._filename] = False

    def add_document(self, name, *fields, **fields_with_content):
        if name in self.documents:
            document = self.documents[name]
        else:
            document = {}
            self.documents[name] = document
        for field in fields:
            if field not in document:
                document[field] = None
        for field, content in fields_with_content:
            document[field] = content

    def get_document(self, name):
        if name in self.documents:
            return self.documents[name]