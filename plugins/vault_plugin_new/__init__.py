from config import VAULT_TEST
from .db_module import DB
from .telegram_module import Telegram
from .vault_module import Vault
from utils import log
from global_variables import RUNNING_FLAG


class Main:
    """
    Главный класс плагина.
    """

    def __init__(self, testing):
        self._db = DB()
        self._vault = Vault(testing)
        self._tg = Telegram()
        # инициализация БД
        self._init_db()

    def _init_db(self):
        if self._db.first_load():
            return
        try:
            flow_timestamp, boris_timestamp = self._vault.get_flow_and_boris_timestamps(responsibly=True)
            godnota_list = [(node_id, title, self._vault.get_last_comment_timestamp(node_id))
                            for node_id, title in self._vault.get_godnota()]  # [(node_id, title, timestamp)...]
        except Exception as e:
            log.log(str(e))
            RUNNING_FLAG.value = False
            return
        self._db.add_document('flow', 'Течение', flow_timestamp)
        self._db.add_document('boris', 'Борис', boris_timestamp)
        for node_id, title, timestamp in godnota_list:
            self._db.add_document(node_id, title, timestamp)

    def sub(self, message):
        self._tg.do_sub(message, self._db.get_topics_titles(), self.sub_next_step)

    def sub_next_step(self, message):
        pass

    def unsub(self):
        pass

    def unsub_next_step(self, message):
        pass

    def scheduled(self):
        pass


vault = Main(VAULT_TEST)

__all__ = ['vault']
