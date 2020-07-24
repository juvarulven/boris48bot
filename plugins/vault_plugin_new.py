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
        pass

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
