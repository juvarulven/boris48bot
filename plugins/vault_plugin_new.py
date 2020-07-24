from typing import List, Dict, Union, Optional
from database import Database
from global_variables import TELEGRAM_BOT, RUNNING_FLAG
from vault_api import Api
from config import VAULT_TEST


class Main:
    """
    Главный класс бота
    """
    def __init__(self, testing):
        self._db = DB()
        self._vault = Vault(testing)
        self._tg = Telegram()
        # инициализация БД
        self._init_db()

    def _init_db(self):
        if not self._db.first_load():


    def sub(self):
        pass

    def unsub(self):
        pass

    def scheduled(self):
        pass


class DB:
    """
    Класс для взаимодействия с БД
    """
    def __init__(self):
        self._db = Database('vault_plugin_new')
        self._flow_timestamp = None
        self._flow_subscribers = []
        self._boris_timestamp = None
        self._boris_subscribers = []
        self._comments: Dict[str, Dict[str, Union[str, List[int]]]] = {}
        # { 'node_id': {'title': 'название', 'timestamp': 'таймстамп', 'subscribers': [телеграм_id...]}... }

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
            if document_name == "flow":
                self._flow_timestamp = document["timestamp"]
                self._flow_subscribers = document["subscribers"]
            elif document_name == "boris":
                self._boris_timestamp = document["timestamp"]
                self._boris_subscribers = document["subscribers"]
            else:
                self._comments[document_name] = document
        return True

    def _update_db(self, target):
        if target == 'flow':
            temp_document = { 'timestamp': self._flow_timestamp,
                              'subscribers': self._flow_subscribers.copy() }
        elif target == 'boris':
            temp_document = { 'timestamp': self._boris_timestamp,
                              'subscribers': self._boris_subscribers.copy() }
        else:
            temp_document = { 'title':       self._comments[target]['title'],
                              'timestamp':   self._comments[target]['timestamp'],
                              'subscribers': self._comments[target]['subscribers'].copy() }
        self._db.update_document(target, fields_with_content=temp_document)
        self._db.save_and_update()

    def get_timestamp(self, target: Union[int, str]) -> Optional[str]:
        """
        Возвращает таймстамп
        :param target: 'flow', 'boris' или id ноды
        :return: таймстамп
        """
        if target == 'flow':
            return self._flow_timestamp
        elif target == 'boris':
            return self._boris_timestamp
        else:
            target = str(target)
            if target.isdigit() and target in self._comments:
                return self._comments[target]['timestamp']

    def set_timestamp(self, target: Union[int, str], timestamp: str) -> None:
        """
        Устанавливает таймстамп и сохраняет в базу
        :param target: 'flow', 'boris' или id ноды
        :param timestamp: таймстамп
        :return:
        """
        if target == 'flow':
            self._flow_timestamp = timestamp
            self._update_db('flow')
        elif target == 'boris':
            self._boris_timestamp = timestamp
            self._update_db('boris')
        else:
            target = str(target)
            if target.isdigit():
                if target in self._comments:
                    self._comments[target]["timestamp"] = timestamp
                    self._update_db(target)

    def get_subscribers(self, target: Union[str, int]) -> List[int]:
        """
        Возвращает список подписчиков
        :param target: 'flow', 'boris' или id ноды Убежища
        :return: список id телеграмма подписчиков
        """
        if target == 'flow':
            return self._flow_subscribers.copy()
        elif target == 'boris':
            return self._boris_subscribers.copy()
        else:
            target = str(target)
            if target in self._comments:
                return self._comments[target]['subscribers'].copy()
            return []


    def add_subscriber(self, target: Union[str, int], telegram_id: int) -> bool:
        """
        Добавляет id телеграмма в список подписчиков и сохраняет в базу
        :param target: 'flow', 'boris' или id ноды
        :param telegram_id: id подписчика
        :return: True если id подписчика не было в списке, иначе False
        """
        successfully = False
        if target == 'flow':
            if telegram_id not in self._flow_subscribers:
                self._flow_subscribers.append(telegram_id)
                self._update_db('flow')
                successfully = True
        elif target == 'boris':
            if telegram_id not in self._boris_subscribers:
                self._boris_subscribers.append(telegram_id)
                self._update_db('boris')
                successfully = True
        else:
            target = str(target)
            if target.isdigit() and target not in self._comments[target]['subscribers']:
                self._comments[target]['subscribers'].append(telegram_id)
                self._update_db(target)
                successfully = True
        return successfully

    def remove_subscriber(self, target: Union[str, int], telegram_id: int) -> bool:
        """
        Удаляет id телеграмма из списка подписчиков и сохраняет в базу
        :param target: 'flow', 'boris' или id ноды
        :param telegram_id: id подписчика
        :return: True, если id телеграмма был в списке, иначе False
        """
        successfully = False
        if target == 'flow':
            if telegram_id in self._flow_subscribers:
                self._flow_subscribers.remove(telegram_id)
                self._update_db('flow')
                successfully = True
        elif target == 'boris':
            if telegram_id in self._boris_subscribers:
                self._boris_subscribers.remove(telegram_id)
                self._update_db('boris')
                successfully = True
        else:
            target = str(target)
            if target.isdigit() and target in self._comments[target]['subscribers']:
                self._comments[target]['subscribers'].remove(telegram_id)
                self._update_db(target)
                successfully = True
        return successfully

    def add_comments(self, node_id: Union[str, int], title: str, timestamp: str) -> None:
        """
        Добавляет ноды с комментариями и сохраняет в базу
        :param node_id: id ноды
        :param title: заголовок ноды
        :param timestamp: таймстамп последнего комментария ноды
        :return:
        """
        node_id = str(node_id)
        if node_id not in self._comments:
            temp_document = {'title': title, 'timestamp': timestamp, 'subscribers': []}
            self._comments[node_id] = temp_document
            self._update_db(node_id)



class Vault:
    """
    Класс для общения с Убежищем
    """
    def __init__(self, testing):
        self._api = Api(testing)

    def check_updates(self, **kwargs):
        pass


class Telegram:
    """
    Класс для взаимодействия с телеграммом
    """
    def __init__(self):
        self._bot = TELEGRAM_BOT.value


vault = Main(VAULT_TEST)

__all__ = ['vault']
