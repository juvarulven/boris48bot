from typing import List, Dict, Tuple, Union, Optional, Callable, Iterator, Any, NamedTuple
from database import Database
from global_variables import TELEGRAM_BOT, RUNNING_FLAG
from vault_api import Api
from vault_api.types import Comment, VaultApiException
from telebot import types as telegram_types
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

    def get_topics_titles(self) -> List[str]:
        """
        Все поля title из базы
        :return: Список заголовков
        """
        return [document.title for document in self._documents.values()]


class VaultCommentsBlock(NamedTuple):
    """
    Блок комментариев пользователя Убежища
    """
    username: str
    user_url: str
    user_comments: List[str]
    with_file: bool
    post_url: str


class VaultImagePost(NamedTuple):
    username: str
    user_url: str
    title: str
    post_url: str
    image_url: str
    description: str


class VaultTextPost(NamedTuple):
    username: str
    user_url: str
    title: str
    post_url: str
    description: str


class VaultOtherPost(NamedTuple):
    username: str
    user_url: str
    post_url: str


class VaultAudioPost(VaultOtherPost):
    pass


class VaultVideoPost(VaultOtherPost):
    pass


class VaultGodnotaPost(NamedTuple):
    title: str
    post_url: str


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

    def get_comments(self, node_id: str, number=10) -> Tuple[List[VaultCommentsBlock], str]:
        """
        Возвращает кортеж из списка комментариев и таймстампа последнего комментария.

        :param node_id: id ноды
        :param number: количество комментариев для обработки
        :return: список VaultCommentsBlock, таймстамп последнего комментария
        """
        comments_obj = self._api.get_comments(node_id, number)
        post_url = self._api.post_url.format(node_id)
        last_timestamp = comments_obj.comments[0].created_at
        comment_objects_list = comments_obj.comments
        return [comment for comment in self._build_comment_list_item(comment_objects_list, post_url)], last_timestamp

    def _build_comment_list_item(self, comments_list: List[Comment], post_url) -> Iterator[VaultCommentsBlock]:
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
            yield VaultCommentsBlock(username, user_url, user_comments, any(with_file), post_url)

    def _generate_user_url(self, username: str) -> str:
        return self._api.url + '~' + username


class Telegram:
    """
    Класс для взаимодействия с телеграммом.
    """

    def __init__(self):
        self._bot = TELEGRAM_BOT.value

    def do_sub(self, message, topics: List[str], handler: Callable[[Any], None]) -> None:
        self.send_keyboard(message, 'На что хотите подписаться?', topics)
        self._bot.register_next_step_handler(message, handler)

    def do_unsub(self, message, topics: List[str], handler: Callable[[Any], None]) -> None:
        self.send_keyboard(message, 'На что хотите подписаться?', topics)
        self._bot.register_next_step_handler(message, handler)

    def send_keyboard(self, message, text: str, buttons: List[str]) -> None:
        buttons.append('Закончить')
        markup = telegram_types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(telegram_types.KeyboardButton(button) for button in buttons)
        self._bot.send_message(message.from_user.id, text, reply_markup=markup)

    def destroy_keyboard(self, message) -> None:
        markup = telegram_types.ReplyKeyboardRemove(selective=False)
        self._bot.send_message(message.from_user.id, 'Рад услужить!', reply_markup=markup)

    def send_message(self, post_obj: Union[VaultImagePost,
                                           VaultTextPost,
                                           VaultAudioPost,
                                           VaultVideoPost,
                                           VaultOtherPost,
                                           VaultCommentsBlock,
                                           VaultGodnotaPost],
                     subscribers: List[Union[str, int]]) -> None:
        """
        Отправляет сообщение в телеграмм.

        :param post_obj: объект поста или блока комментариев для Бориса
        :param subscribers: подписчики
        :return:
        """
        obj_type = type(post_obj)
        if obj_type == VaultImagePost:
            message = self._generate_image_message(post_obj)
            self._send_photo(subscribers, post_obj.image_url, message)
            return
        elif obj_type == VaultTextPost:
            message = self._generate_text_message(post_obj)
        elif obj_type == VaultAudioPost:
            message = self._generate_audio_message(post_obj)
        elif obj_type == VaultVideoPost:
            message = self._generate_video_message(post_obj)
        elif obj_type == VaultOtherPost:
            message = self._generate_other_message(post_obj)
        elif obj_type == VaultCommentsBlock:
            message = self._generate_boris_message(post_obj)
        elif obj_type == VaultGodnotaPost:
            message = self._generate_godnota_message(post_obj)
        else:
            raise VaultPluginException('Попытка послать в Тлеграмм сообщение неизвестного типа')
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
    def _generate_image_message(obj: VaultImagePost) -> str:
        """
        Генерирует текстовое описания для сообщения типа 'image'.

        :param obj: объект поста изображения
        :return: текст опистания
        """
        template = '\n[{}]({})\n_Вот чем в Течении делится_ [~{}]({}) _(и, возможно, это еще не все)_'
        with_description = '\n_да вдобавок пишет:_\n\n{}'
        message = template.format(de_markdown(obj.title), obj.post_url, de_markdown(obj.username), obj.user_url)
        description = obj.description
        if description:
            message += with_description.format(de_markdown(description))
        return message

    @staticmethod
    def _generate_text_message(obj: VaultTextPost) -> str:
        """
        Генерирует текст для сообщения типа 'text'.

        :param obj: объект текстового поста
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится мыслями в Течении:_\n\n[{}]({})\n{}'
        return template.format(de_markdown(obj.username),
                               obj.user_url,
                               de_markdown(obj.title),
                               obj.post_url,
                               de_markdown(obj.description))

    @staticmethod
    def _generate_audio_message(obj: VaultAudioPost) -> str:
        """
        Генерирует текст для сообщения типа 'audio'.

        :param obj: объект аудиопоста
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится_ [аудиозаписью]({}) _в Течении (а может и не одной)._'
        return template.format(de_markdown(obj.username), obj.user_url, obj.post_url)

    @staticmethod
    def _generate_video_message(obj: VaultVideoPost) -> str:
        """
        Генерирует текст для сообщения типа 'video'.

        :param obj: объект видеопоста
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится_ [видеозаписью]({}) _в Течении._'
        return template.format(de_markdown(obj.username), obj.user_url, obj.post_url)

    @staticmethod
    def _generate_other_message(obj: VaultOtherPost) -> str:
        """
        Генерирует текст для сообщения типа 'other'.

        :param obj: объект поста типа 'other'
        :return: текст сообщения
        """
        template = '[~{}]({}) _делится чем-то_ [неординарным]({}) _в Течении._'
        return template.format(de_markdown(obj.username), obj.user_url, obj.post_url)

    @staticmethod
    def _generate_boris_message(obj: VaultCommentsBlock) -> str:
        """
        Генерирует текст для сообщения типа 'boris'.

        :param obj: объект блока комментариев для Бориса
        :return: текст сообщения
        """
        template = '_Вот что_ [~{}]({}) _пишет_ [Борису]({})_:_\n\n{}'
        separator = '\n\n_и продолжает:_\n\n'
        with_f = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        comments = list(map(de_markdown, obj.user_comments))
        comments = separator.join(comments)
        message = template.format(de_markdown(obj.username), obj.user_url, obj.post_url, comments)
        if obj.with_file:
            message += with_f
        return message

    @staticmethod
    def _generate_godnota_message(obj: VaultGodnotaPost) -> str:
        """
        Генерирует текст для сообщения типа 'godnota':

        :param obj: объект поста убежища
        :return: текст сообщения
        """
        template = '_В коллекции_ [{}]({}) _появилось что-то новенькое_'
        return template.format(de_markdown(obj.title), obj.post_url)


vault = Main(VAULT_TEST)

__all__ = ['vault']
