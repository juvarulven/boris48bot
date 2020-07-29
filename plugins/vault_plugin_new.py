from typing import List, Dict, Tuple, Union, Optional, Callable, Iterator, Any, NamedTuple
from database import Database
from global_variables import TELEGRAM_BOT, RUNNING_FLAG
from vault_api import Api
from vault_api.types import Comment, VaultApiException
from config import VAULT_TEST
from utils import log
from utils.string_functions import de_markdown


class VaultPluginException(Exception):
    def __init__(self, message):
        super(VaultPluginException, self).__init__('VaultPlugin: ', message)


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
            flow_timestamp, boris_timestamp = self._vault.get_flow_and_boris_timestamps()
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

    def sub(self):
        pass

    def unsub(self):
        pass

    def scheduled(self):
        pass


class DBDocumentFields(NamedTuple):
    """
    Поля документа базы данных.
    """
    title: str
    timestamp: str
    subscribers: List[int]


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


class CommentsBlock(NamedTuple):
    """
    Блок комментариев пользователя Убежища
    """
    username: str
    user_url: str
    user_comments: List[str]
    with_file: bool


class Vault:
    """
    Класс для общения с Убежищем.
    """
    def __init__(self, testing):
        self._api = Api(testing)

    @staticmethod
    def _try_it_5_times(what_to_do: Callable[[Any], Any], *args, **kwargs) -> Any:
        """
        Пытается выполнить функцию пять раз. В случае неудачи бросает исключение.

        :param what_to_do: функция, которую следует выполнить 5 раз
        :param args: позиционные аргументы для этой функции
        :param kwargs: именованные аргументы для этой функции
        :return: результат выполнения функции
        """
        successfully = False
        try_counter = 5
        response = None
        error = None
        while try_counter:
            try:
                response = what_to_do(*args, **kwargs)
                successfully = True
            except VaultApiException as error:
                try_counter -= 1
        if not successfully:
            raise VaultPluginException('Ошибка при попытке сделать 5 раз {}:\n{}: {}'.format(what_to_do.__name__,
                                                                                             error.__class__.__name__,
                                                                                             error))
        return response

    def get_flow_and_boris_timestamps(self, responsibly=False) -> Tuple[str, str]:
        """
        Получает последние таймстампы Течения и Бориса.

        :param responsibly: если True пытается сделать это 5 раз
        :return: таймстамп Течения, таймстамп Бориса
        """
        if responsibly:
            stats = self._try_it_5_times(self._api.get_stats)
        else:
            stats = self._api.get_stats()
        return stats.timestamps_flow, stats.timestamps_boris

    def get_godnota(self) -> Iterator[Tuple[str, str]]:
        """
        Генератор годноты.

        :return: id ноды, заголовок
        """
        godnota = self._try_it_5_times(self._api.get_godnota)
        for title in godnota:
            yield str(godnota[title]), title

    def get_last_comment_timestamp(self, node_id: str) -> str:
        """
        Пытается 5 раз получить таймстамп последнего комментария ноды.

        :param node_id: id ноды
        :return: таймстамп
        """
        comment_tuple = self._try_it_5_times(self.get_comments, node_id, 1)
        return comment_tuple[1]

    def get_comments(self, node_id: str, number=10) -> Tuple[List[CommentsBlock], str]:
        """
        Возвращает кортеж из списка комментариев и таймстампа последнего комментария.

        :param node_id: id ноды
        :param number: количество комментариев для обработки
        :return: список CommentsBlock, таймстамп последнего комментария
        """
        comments_obj = self._api.get_comments(node_id, number)
        last_timestamp = comments_obj.comments[0].created_at
        comment_objects_list = comments_obj.comments
        return [comment for comment in self._build_comment_list_item(comment_objects_list)], last_timestamp

    def _build_comment_list_item(self, comments_list: List[Comment]) -> Iterator[CommentsBlock]:
        while comments_list:
            comment = comments_list.pop()
            username = comment.user.username
            user_url = self._generate_user_url(username)
            with_file = [bool(comment.files)]
            user_comments = [comment.text]
            while comments_list and username == comments_list[-1].user.username:
                comment = comments_list.pop()
                user_comments.append(comment.text)
                with_file.append(bool(comment.files))
            yield CommentsBlock(username, user_url, user_comments, any(with_file))

    def _generate_user_url(self, username: str) -> str:
        return self._api.url + '~' + username


class Telegram:
    """
    Класс для взаимодействия с телеграммом.
    """

    def __init__(self):
        self._bot = TELEGRAM_BOT.value

    def send_message(self, message_type: str, subscribers: List[Union[str, int]], *args, **kwargs) -> None:
        """
        Отправляет сообщение в телеграмм.

        :param message_type: тип сообщения
        :param subscribers: подписчики
        :param args: аргументы для функций шаблонов
        :param kwargs: аргументы для функций шаблонов. Для типа 'image' обязательно должен быть аргумент image_url=
        :return:
        """
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

    def _send_text(self, subscribers: List[Union[str, int]], text: str) -> None:
        """
        Отправляет текстовое сообщение подписчикам в телеграмм.

        :param subscribers: список id телеграмма
        :param text: текст сообщения
        :return:
        """
        for addressee in subscribers:
            try:
                self._bot.send_message(addressee, text, parse_mode='Markdown')
            except Exception as error:
                error_message = 'vault_plugin: Ошибка при попытке отправить сообщение в телеграмм: ' + str(error)
                log.log(error_message)

    def _send_photo(self, subscribers: List[Union[str, int]], url: str, text: str):
        """
        Отправляет фото подписчикам в телеграмм.

        :param subscribers: список id телеграмма
        :param url: url фото
        :param text: текстовое опистание
        :return:
        """
        for addressee in subscribers:
            try:
                self._bot.send_photo(addressee, url, caption=text, parse_mode='Markdown')
            except Exception as error:
                error_message = 'vault_plugin: Ошибка при попытке отправить фото в телеграмм: ' + str(error)
                log.log(error_message)

    @staticmethod
    def _generate_image_message(title: str, url: str, username: str, user_url: str, description: str = "") -> str:
        """
        Генерирует текстовое описания для сообщения типа 'image'.

        :param title: заголовок поста Убежища
        :param url: ссылка на пост Убежища
        :param username: ник запостившего
        :param user_url: ссылка на запостившего
        :param description: описание к посту Убежища
        :return: текст опистания
        """
        template = '\n[{}]({})\n_Вот чем в Течении делится_ [~{}]({}) _(и, возможно, это еще не все)_'
        with_description = '\n_да вдобавок пишет:_\n\n{}'
        message = template.format(de_markdown(title), url, de_markdown(username), user_url)
        if description:
            message += with_description.format(de_markdown(description))
        return message

    @staticmethod
    def _generate_text_message(username: str, user_url: str, title: str, url: str, description: str) -> str:
        """
        Генерирует текст для сообщения типа 'text'.

        :param username: ник запостившего
        :param user_url: ссылка на запостившего
        :param title: заголовок поста Убежища
        :param url: ссылка на пост Убежища
        :param description: тело поста Убежища
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится мыслями в Течении:_\n\n[{}]({})\n{}'
        return template.format(de_markdown(username), user_url, de_markdown(title), url, de_markdown(description))

    @staticmethod
    def _generate_audio_message(username: str, user_url: str, url: str) -> str:
        """
        Генерирует текст для сообщения типа 'audio'.

        :param username: ник запостившего
        :param user_url: ссылка на запостившего
        :param url: ссылка на пост Убежища
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится_ [аудиозаписью]({}) _в Течении (а может и не одной)._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_video_message(username: str, user_url: str, url: str) -> str:
        """
        Генерирует текст для сообщения типа 'video'.

        :param username: ник запостившего
        :param user_url: ссылка на запостившего
        :param url: ссылка на пост Убежища
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится_ [видеозаписью]({}) _в Течении._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_other_message(username: str, user_url: str, url: str) -> str:
        """
        Генерирует текст для сообщения типа 'other'.

        :param username: ник запостившего
        :param user_url: ссылка на запостившего
        :param url: ссылка на пост убежища
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится чем-то_ [неординарным]({}) _в Течении._'
        return template.format(de_markdown(username), user_url, url)

    @staticmethod
    def _generate_boris_message(username, user_url, url, comments: List[str], with_files=False) -> str:
        """
        Генерирует текст для сообщения типа 'boris'.

        :param username: ник комментирующего
        :param user_url: ссылка на комментирующего
        :param url: ссылка на Бориса
        :param comments: список комментариев
        :param with_files: прикреплен ли файл
        :return: текст сообщения
        """
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
        """
        Генерирует текст для сообщения типа 'godnota':

        :param title: заголовок поста с годнотой
        :param url: ссылка на пост Убежища
        :return: текст сообщения
        """
        template = '_В коллекции_ [{}]({}) _появилось что-то новенькое_'
        return template.format(de_markdown(title), url)


vault = Main(VAULT_TEST)

__all__ = ['vault']
