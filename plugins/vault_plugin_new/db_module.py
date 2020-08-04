from database import Database
from .plugin_types import DBDocumentFields
from typing import Dict, Optional, List


class DB:
    """
    Класс для взаимодействия с БД.
    """

    def __init__(self):
        self._db = Database('vault_plugin_new')
        self._documents: Dict[str, DBDocumentFields] = {}

    def first_load(self) -> bool:
        """
        Загружает таймстампы и списки подписчиков в свою память из базы.

        :return: False если в базе ничего нет
        """
        document_names = self._db.get_document_names()
        if not document_names:
            return False
        for document_name in document_names:
            document = self._db.get_document(document_name)
            self._documents[document_name] = DBDocumentFields(document['title'],
                                                              document['timestamp'],
                                                              document['subscribers'])
        return True

    def _update_db(self, target):
        if target in self._documents:
            tmp_document = {'title': self._documents[target].title,
                            'timestamp': self._documents[target].timestamp,
                            'subscribers': self._documents[target].subscribers}
            self._db.update_document(target, fields_with_content=tmp_document)
            self._db.save_and_update()

    def get_timestamp(self, target: str) -> Optional[str]:
        """
        Возвращает таймстамп.

        :param target: 'flow', 'boris' или id ноды
        :return: таймстамп
        """
        return self._documents[target].timestamp if target in self._documents else None

    def set_timestamp(self, target: str, timestamp: str) -> None:
        """
        Устанавливает таймстамп и сохраняет в базу.

        :param target: 'flow', 'boris' или id ноды
        :param timestamp: таймстамп
        :return:
        """
        if target in self._documents:
            self._documents[target]._replace(timestamp=timestamp)
            self._update_db(target)

    def get_subscribers(self, target: str) -> List[int]:
        """
        Возвращает список подписчиков.

        :param target: 'flow', 'boris' или id ноды Убежища
        :return: список id телеграмма подписчиков
        """
        return self._documents[target].subscribers.copy()

    def add_subscriber(self, target: str, telegram_id: int) -> bool:
        """
        Добавляет id телеграмма в список подписчиков и сохраняет в базу.

        :param target: 'flow', 'boris' или id ноды
        :param telegram_id: id подписчика
        :return: True если id подписчика не было в списке, иначе False
        """
        if telegram_id not in self._documents[target].subscribers:
            self._documents[target].subscribers.append(telegram_id)
            self._update_db(target)
            return True
        return False

    def remove_subscriber(self, target: str, telegram_id: int) -> bool:
        """
        Удаляет id телеграмма из списка подписчиков и сохраняет в базу.

        :param target: 'flow', 'boris' или id ноды
        :param telegram_id: id подписчика
        :return: True, если id телеграмма был в списке, иначе False
        """
        if telegram_id in self._documents[target].subscribers:
            self._documents[target].subscribers.remove(telegram_id)
            self._update_db(target)
            return True
        return False

    def add_document(self, node: str, title: str, timestamp: str) -> None:
        """
        Добавляет ноды с комментариями и сохраняет в базу.

        :param node: id ноды
        :param title: заголовок ноды
        :param timestamp: таймстамп последнего комментария ноды
        :return:
        """
        if node not in self._documents:
            self._documents[node] = DBDocumentFields(title, timestamp, [])
            self._update_db(node)

    def get_comments_nodes(self) -> list:
        """
        Возвращает список кортежей с id нод и их заголовками.

        :return: [ ('node_id', 'title')... ]
        """
        node_ids_and_titles = []
        for document_name, document in self._documents.items():
            if document_name.isdigit():
                node_ids_and_titles.append((document_name, document.title))
        return node_ids_and_titles

    def get_topics_titles(self) -> List[str]:
        """
        Все поля title из базы
        :return: Список заголовков
        """
        return [document.title for document in self._documents.values()]

    def get_document_name_by_title(self, title: str) -> Optional[str]:
        for document_name, document in self._documents.items():
            if document.title == title:
                return document_name
