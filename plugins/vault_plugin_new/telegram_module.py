from utils import log
from utils.string_functions import de_markdown
from global_variables import TELEGRAM_BOT
from typing import List, Callable, Any, Union
from telebot import types as telegram_types
from .plugin_types import VaultImagePost, VaultTextPost, VaultAudioPost, VaultVideoPost, VaultOtherPost
from .plugin_types import VaultCommentsBlock, VaultGodnotaPost, VaultPluginException


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
