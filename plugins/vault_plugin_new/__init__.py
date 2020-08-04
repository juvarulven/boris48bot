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
        topics = self._db.get_topics_titles()
        topics.append('Закончить')
        self._tg.do_sub(message, topics, self.sub_next_step)

    def sub_next_step(self, message):
        telegram_id = message.from_user.id
        topic = message.text
        if topic == 'Закончить':
            self._tg.destroy_keyboard(message)
            return
        document_name = self._db.get_document_name_by_title(topic)
        if document_name is None:
            self._tg.send_text([telegram_id], 'Не могу этого сделать!')
        elif not self._db.add_subscriber(document_name, telegram_id):
            self._tg.send_text([telegram_id], 'Вы уже подписаны на топик ' + topic)
        else:
            self._tg.send_text([telegram_id], 'Теперь вы подписаны на топик ' + topic)
        self._tg.next_step(message, self.sub_next_step)

    def unsub(self, message):
        topics = self._db.get_topics_titles()
        topics.append('Закончить')
        self._tg.do_unsub(message, topics, self.unsub_next_step)

    def unsub_next_step(self, message):
        telegram_id = message.from_user.id
        topic = message.text
        if topic == 'Закончить':
            self._tg.destroy_keyboard(message)
            return
        document_name = self._db.get_document_name_by_title(topic)
        if document_name is None:
            self._tg.send_text([telegram_id], 'Не могу этого сделать!')
        elif not self._db.remove_subscriber(document_name, telegram_id):
            self._tg.send_text([telegram_id], 'Вы не были подписаны на топик ' + topic)
        else:
            self._tg.send_text([telegram_id], 'Вы больше не будете получать обновления топика ' + topic)
        self._tg.next_step(message, self.unsub_next_step)

    def scheduled(self):
        pass


vault = Main(VAULT_TEST)

__all__ = ['vault']
