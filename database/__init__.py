import bson
import os.path
import time
from typing import Any, Dict, Set, Union, Optional, Callable


class Database:
    file_lock = {}

    def __init__(self, collection: str):
        self._filename = collection + '.bson'
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

    def add_document(self, name: Union[str, int], *fields: str, **fields_with_content: Any) -> None:
        additional_dict = {}
        for field in fields:
            additional_dict[field] = None
        fields_with_content.update(**additional_dict)
        if name not in self._collection:
            self._collection[name] = {}
        self._collection[name].update(**fields_with_content)

    def get_document(self, name: Union[str, int]) -> dict:
        if name in self._collection:
            return self._collection[name].copy()

    def get_documents_names(self) -> Set[Union[str, int]]:
        return set(self._collection.keys())

    def get_document_names_with_condition(self, **fields_and_functions: Callable[[str], bool]) -> Set[Union[int, str]]:
        match = set()
        total_conditions = len(fields_and_functions)
        for document_name, content in self._collection:
            matches = total_conditions
            for field, func in fields_and_functions:
                if field in content:
                    result = func(content[field])
                    if isinstance(result, bool) and result:
                        matches -= 1
            if not matches:
                match.add(document_name)
        return match
