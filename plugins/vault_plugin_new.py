from typing import List, Dict, Union, Optional
from database import Database
from global_variables import TELEGRAM_BOT, RUNNING_FLAG
from vault_api import Api
from config import VAULT_TEST
from utils import log
from utils.string_functions import de_markdown


class Main:
    """
    Главный класс плагина
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

    def get_comments_nodes(self) -> list:
        """
        Возвращает список кортежей с id нод и их заголовками
        :return: [ ('node_id', 'title')... ]
        """
        nodes_list = []
        for node_id in self._comments:
            nodes_list.append((node_id, self._comments[node_id]['title']))
        return nodes_list


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

    def send_message(self, message_type: str, subscribers: List[Union[str, int]], *args, **kwargs):
        if message_type == 'image' and 'image_url' in kwargs:
            image_url = kwargs.pop('image_url')
            message = self._generate_image_message(*args, **kwargs)
            self._send_photo(subscribers, image_url, message)
            return
        elif message_type == 'text':
            message = self._generate_text_message(*args, **kwargs)
        elif message_type == 'audio':
            message = self._generate_audio_message(*args, **kwargs)
        elif message_type == 'video':
            message = self._generate_video_message(*args, **kwargs)
        elif message_type == 'other':
            message = self._generate_other_message(*args, **kwargs)
        elif message_type == 'boris':
            message = self._generate_boris_message(*args, **kwargs)
        elif message_type == 'godnota':
            message = self._generate_godnota_message(*args, **kwargs)
        else:
            return
        self._send_text(subscribers, message)

    def _send_text(self, subscribers: List[Union[str, int]], text: str):
        for addressee in subscribers:
            try:
                self._bot.send_message(addressee, text, parse_mode='Markdown')
            except Exception as error:
                error_message = 'vault_plugin: Ошибка при попытке отправить сообщение в телеграмм: ' + str(error)
                log.log(error_message)

    def _send_photo(self, subscribers: List[Union[str, int]], url: str, text: str):
        for addressee in subscribers:
            try:
                self._bot.send_photo(addressee, url, caption=text, parse_mode='Markdown')
            except Exception as error:
                error_message = 'vault_plugin: Ошибка при попытке отправить фото в телеграмм: ' + str(error)
                log.log(error_message)

    @staticmethod
    def _generate_image_message(title: str, url: str, username: str, user_url: str, description: str = "") -> str:
        template = '\n[{}]({})\n_Вот чем в Течении делится_ [~{}]({}) _(и, возможно, это еще не все)_'
        with_description = '\n_да вдобавок пишет:_\n\n{}'
        message = template.format(de_markdown(title), url, de_markdown(username), user_url)
        if description:
            message += with_description.format(de_markdown(description))
        return message

    @staticmethod
    def _generate_text_message(username: str, user_url: str, title: str, url: str, description: str) -> str:
        template = '[~{}]({}) _делится мыслями в Течении:_\n\n[{}]({})\n{}'
        return template.format(de_markdown(username), user_url, de_markdown(title), url, de_markdown(description))

    @staticmethod
    def _generate_audio_message(username: str, user_url: str, url: str) -> str:
        template = '[~{}]({}) _делится_ [аудиозаписью]({}) _в Течении (а может и не одной)._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_video_message(username: str, user_url: str, url: str) -> str:
        template = '[~{}]({}) _делится_ [видеозаписью]({}) _в Течении._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_other_message(username: str, user_url: str, url: str) -> str:
        template = '[~{}]({}) _делится чем-то_ [неординарным]({}) _в Течении._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_boris_message(username, user_url, url, comments: List[str], with_files = False) -> str:
        template = '_Вот что_ [~{}]({}) _пишет_ [Борису]({})_:_\n\n{}'
        separator = '\n\n_и продолжает:_\n\n'
        with_f = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        comments = list(map(de_markdown, comments))
        comments = separator.join(comments)
        message = template.format(de_markdown(username), user_url, url, comments)
        if with_files:
            message += with_f
        return message

    @staticmethod
    def _generate_godnota_message(title, url) -> str:
        template = '_В коллекции_ [{}]({}) _появилось что-то новенькое_'
        return template.format(de_markdown(title), url)



vault = Main(VAULT_TEST)

__all__ = ['vault']
