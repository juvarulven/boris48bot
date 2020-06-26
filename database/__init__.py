"""
Модуль квази-базы данных
По умолчанию сохраняются в res/bsons/

Глоссарий:
Документ -- словарь вида {имя_поля: значение}. Имя_поля может быть только типа str, ибо нефиг. Значение -- любого типа
Коллекция -- словарь вида {имя_документа: документ}. Имя_документа может быть только типов int и str,
ибо, опять же, нефиг
"""

import bson
import os.path
import time
from typing import Any, Dict, List, Set, Union, Optional, Callable


class Database:
    """
    Объект коллекции квази-базы данных.
    Методы:
    save_and_update: сохраняет коллекцию на диск
    update_document: обновляет документ внутри себя
    get_document: возвращает документ
    get_document_names: возвращает имена всех документов в коллекции
    get_document_names_with_conditions: возвращает имена документов,
    в которых сработало условие для отдельных полей
    """
    file_lock = {}

    def __init__(self, collection: str):
        """
        Создание объекта коллекции. Если коллекция с названием из collection есть на диске -- будет загружена.
        Если нет -- будет создана в памяти.

        :param collection: название для коллекции.
        """
        self._filename = FILE_PATH + collection + '.bson'
        if self._filename not in self.__class__.file_lock:
            self.__class__.file_lock[self._filename] = False
        self._collection = None
        self._init_collection()

    def _load(self) -> Optional[Dict[Any, dict]]:
        if os.path.exists(self._filename):
            with open(self._filename, 'rb') as collection_file:
                collection = bson.loads(collection_file.read())
            return collection
        else:
            return None

    def _init_collection(self) -> None:
        collection = self._load()
        if collection is None:
            self._collection = {}
        else:
            self._collection = collection

    def save_and_update(self) -> None:
        """
        Сохраняет коллекцию на диск. Работает так: загружает коллекцию с диска, если она там есть,
        Обновляет своими данными, сохраняет на диск.

        :return: None
        """
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

    def update_document(self, document_name: Union[str, int], fields: Optional[List[str]] = None,
                        fields_with_content: Optional[Dict[str, Any]] = None) -> None:
        """
        Обновляет документ в коллекции (или создает, если такого нет)

        :param document_name: Имя документа.
        :param fields: список имен полей, которым будет присвоено значение None в документе
        :param fields_with_content: словарь имен полей со значениями.
        :return: None
        """
        if fields_with_content is None:
            fields_with_content = {}
        if fields is not None:
            for field in fields:
                fields_with_content[field] = None
        if document_name not in self._collection:
            self._collection[document_name] = {}
        self._collection[document_name].update(fields_with_content)

    def get_document(self, name: Union[str, int]) -> Optional[dict]:
        """
        Возвращает документ.

        :param name: имя документа
        :return: документ, если таковой имеется, либо None
        """
        if name in self._collection:
            return self._collection[name].copy()

    def get_document_names(self, conditions: Optional[Dict[str, Callable[[str], bool]]] = None) -> Set[Union[int, str]]:
        """
        Возвращает имена документов, поля которых удовлетворяют условию, если оно задано, иначе все имена.
        Условие -- функция, принимающая в качестве аргумента содержимое поля и возвращающая булевое значение
        Например:
        obj.get_document_names_with_condition({'id': lambda _: True})
        Вернет имена документов, в которых есть поле 'id'
        obj.get_document_names_with_condition({'age': lambda x: x > 18})
        Вернет имена документов, в которых значение в поле 'age' больше 18

        :param conditions: словарь имен полей с функцией для проверки
        :return: Множество имен документов
        """
        if conditions is None:
            return set(self._collection.keys())
        match = set()
        total_conditions = len(conditions)
        for document_name, content in self._collection.items():
            matches = total_conditions
            for field, func in conditions.items():
                if field in content:
                    result = func(content[field])
                    if isinstance(result, bool) and result:
                        matches -= 1
            if not matches:
                match.add(document_name)
        return match


FILE_PATH = 'res/bsons/'


__all__ = ['Database']

if __name__ == '__main__':
    FILE_PATH = ''
    db = Database('test')
    db.update_document('test_document', ['uno', 'dos'], {'with_int': 123, 'with_str': 'blah', 'dict_field': {123: 123}})
    db.save_and_update()
    print(db.get_document('test_document'))
    print(db.get_document('abrahadabra'))
    print(db.get_document_names())
    print(db.get_document_names({'with_int': lambda x: x == 123, 'with_str': lambda x: x == 'blahblahblah'}))
    print(db.get_document_names({'with_int': lambda x: x == 123, 'with_str': lambda x: x == 'blah'}))
    print(db.get_document_names({'is': lambda x: x == 'blahblah'}))
    db = Database('test')
    print(db.get_document('test_document'))
