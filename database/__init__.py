import bson
import os.path
import time


class Database:
    file_lock = {}

    def __init__(self, collection):
        self._filename = collection + '.bson'
        self.__class__.file_lock[self._filename] = False
        self._collection = None
        self._init_collection()

    def _load(self):
        if os.path.exists(self._filename):
            with open(self._filename, 'rb') as collection_file:
                collection = bson.loads(collection_file.read())
            return collection
        else:
            return None

    def _init_collection(self):
        collection = self._load()
        if collection is None:
            self._collection = {}
        else:
            self._collection = collection

    def save_and_update(self):
        while self.__class__.file_lock[self._filename]:  # Ожидает отпускания блокировки файла
            time.sleep(0.01)
        self.__class__.file_lock[self._filename] = True  # Выставляет блокировку файла
        current_collection = self._collection  # Сохраняет текущую внутреннюю коллекцию во временный словарь
        self._init_collection()  # Обновляет внутреннюю коллекцию на случай, если файл был кем-то перезаписан
        for document in current_collection:  # Проход по документам текущей коллекции
            if document not in self._collection:  # Если документ не присутствует в коллекции:
                self._collection[document] = {}  # Создает его во внутренней коллекции как пустой словарь
            self._collection[document].update(**current_collection[document])  # Обновляет документ
        with open(self._filename, 'wb') as collection_file:  # Сохраняет изменения в файл
            collection_file.write(bson.dumps(self._collection))
        self.__class__.file_lock[self._filename] = False  # Отпускает блокировку

    def add_document(self, name, *fields, **fields_with_content):
        additional_dict = {}
        for field in fields:
            additional_dict[field] = None
        fields_with_content.update(**additional_dict)
        if name not in self._collection:
            self._collection[name] = {}
        self._collection[name].update(**fields_with_content)

    def get_document(self, name):
        if name in self._collection:
            return self._collection[name].copy()
