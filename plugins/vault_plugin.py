from typing import Union, Optional, Dict, List, Callable, Any
from telebot import types as markups
from database import Database
from vault_api import Api
from vault_api.types import DiffPost, Comment
from utils import log
from global_variables import RUNNING_FLAG, TELEGRAM_BOT
from config import VAULT_TEST


class Vault:
    def __init__(self, testing):
        self._api = Api(testing=testing)
        self._flow_messages: List[DiffPost] = []
        self._boris_messages: List[Comment] = []
        self._godnota_updates: List[str] = []
        self._db = Database('vault_plugin')
        self._last_updates: Dict[str, Union[Dict[Union[str, int],
                                                 Union[Optional[str],
                                                       List[int],
                                                       Dict[str,
                                                            Union[str, List[int]]]]],
                                            Optional[int]]] = \
            {'flow': {'timestamp': None, 'subscribers': []},
             'boris': {'timestamp': None, 'subscribers': []},
             'comments': {}, 'comments_count': None}
        self._godnota: Optional[Dict[str, int]] = None
        self._init_database()

    @staticmethod
    def _do_it_5_times(what_to_do: Callable[[Any], Any], *args: [Any], **kwargs: [Any]) -> Any:
        response = None
        try_counter = 5
        while response is None and try_counter:
            response = what_to_do(*args, **kwargs)
            try_counter -= 1
        if response is None:
            RUNNING_FLAG.value = False
            log.log('vault_plugin: ошибка при попытке сделать {} 5 раз'.format(what_to_do.__name__))
            return
        return response

    def _init_database(self) -> None:
        need_update_db = False
        last_updates = self._db.get_document('last_updates')
        if last_updates is None:
            need_update_db = True
            stats = self._do_it_5_times(self._api.get_stats)
            if stats is None:
                return
            self._last_updates['comments_count'] = stats.comments_total
            self._last_updates['flow']['timestamp'] = stats.timestamps_flow
            self._last_updates['boris']['timestamp'] = stats.timestamps_boris
        else:
            tmp_dict = {}
            for key in last_updates['comments']:
                tmp_dict[int(key)] = last_updates['comments'][key]
            del(last_updates['comments'])
            last_updates['comments'] = tmp_dict
            self._last_updates = last_updates
        self._godnota = self._do_it_5_times(self._api.get_godnota)
        if self._godnota is None:
            log.log('vault_plugin: Не удалось получить годноту за пять попыток')
            return
        for title, post_id in self._godnota.items():
            if post_id not in self._last_updates['comments']:
                need_update_db = True
                comments = self._do_it_5_times(self._api.get_comments, post_id, 1)
                if comments is None:
                    log.log('vault_plugin: не удалось получить комментарии из {} за пять попыток'.format(title))
                    return
                self._last_updates['comments'][post_id]: Dict[str, Union[str, List[int]]] = {}
                self._last_updates['comments'][post_id]['timestamp'] = comments.comments[0].created_at
                self._last_updates['comments'][post_id]['subscribers'] = []
        if need_update_db:
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()

    def _change_subscribers_list(self, target: Union[str, int], telegram_id: int, add: bool) -> bool:
        need_update_db = False
        if target in self._last_updates:
            target = self._last_updates[target]['subscribers']
            if add and telegram_id not in target:
                need_update_db = True
                target.append(telegram_id)
            if not add and telegram_id in target:
                need_update_db = True
                target.remove(telegram_id)
        elif target in self._last_updates['comments']:
            target = self._last_updates['comments'][target]['subscribers']
            if add and telegram_id not in target:
                need_update_db = True
                target.append(telegram_id)
            if not add and telegram_id in target:
                need_update_db = True
                target.remove(telegram_id)
        else:
            raise AssertionError('vault_plugin: ' + str(target) + 'отсутствует в базе')
        if need_update_db:
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()
        return need_update_db

    def _check_updates(self) -> None:
        stats = self._api.get_stats()
        need_update_db = []
        if stats is not None:
            need_update_db = [self._update_flow(stats.timestamps_flow),
                              self._update_boris(stats.timestamps_boris, stats.comments_total)]
        need_update_db.append(self._update_godnota())
        if stats.comments_total != self._last_updates['comments_count']:
            self._last_updates['comments_count'] = stats.comments_total
            need_update_db.append(True)
        if any(need_update_db):
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()

    def _update_flow(self, current_timestamp: str) -> bool:
        last_timestamp = self._last_updates['flow']['timestamp']
        if last_timestamp < current_timestamp:
            diff = self._api.get_diff(last_timestamp, last_timestamp)
            if diff is None:
                return False
            self._last_updates['flow']['timestamp'] = current_timestamp
            self._flow_messages = diff.before
            return True
        return False

    def _update_boris(self, current_timestamp: str, current_comments_count: int) -> bool:
        last_timestamp = self._last_updates['boris']['timestamp']
        comments_count = current_comments_count - self._last_updates['comments_count'] + 5
        if last_timestamp < current_timestamp:
            comments = self._update_comments(self._api.boris_node, last_timestamp, comments_count)
            if not comments:
                return False
            self._last_updates['boris']['timestamp'] = current_timestamp
            self._boris_messages = comments
            return True
        return False

    def _update_comments(self, node: int, last_timestamp: str, comments_count: int) -> List[Comment]:
        comments_list = []
        comments = self._api.get_comments(node, comments_count)
        if comments is None:
            return comments_list
        for comment in comments.comments:
            if comment.created_at <= last_timestamp:
                break
            comments_list.append(comment)
        return comments_list

    def _update_godnota(self) -> bool:
        need_update_db = False
        recent = self._api.get_recent()
        if recent is None:
            return False
        for node in recent:
            node_id = node.id
            if node_id in self._last_updates['comments']:
                current_timestamp = node.commented_at
                current = self._last_updates['comments'][node_id]
                last_timestamp = current['timestamp']
                if current['subscribers'] and current_timestamp > last_timestamp:
                    need_update_db = True
                    current['timestamp'] = current_timestamp
                    self._godnota_updates.append(node.title)
        return need_update_db

    def sub(self, message):
        telegram_id = message.from_user.id
        markup = markups.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(markups.KeyboardButton('Течение'), markups.KeyboardButton('Борис'),
                   *[markups.KeyboardButton(target) for target in self._godnota],
                   markups.KeyboardButton('Закончить'))
        TELEGRAM_BOT.value.send_message(telegram_id, 'На что хотите подписаться?', reply_markup=markup)
        TELEGRAM_BOT.value.register_next_step_handler(message, self.sub_next_step)

    def sub_next_step(self, message):
        text = message.text
        telegram_id = message.from_user.id
        if text == 'Течение':
            result = self._change_subscribers_list('flow', telegram_id, add=True)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы будете получать обновления Течения')
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы уже подписаны на Течение')
        elif text == 'Борис':
            result = self._change_subscribers_list('boris', telegram_id, add=True)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы уже подписаны на Бориса')
        elif text in self._godnota:
            result = self._change_subscribers_list(self._godnota[text], telegram_id, add=True)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы будете получать обновления из ' + text)
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы уже подписаны на ' + text)
        elif text == 'Закончить':
            markup = markups.ReplyKeyboardRemove(selective=False)
            TELEGRAM_BOT.value.send_message(message.from_user.id, 'Рад услужить', reply_markup=markup)
            return
        else:
            TELEGRAM_BOT.value.send_message(telegram_id, 'Нельзя подписаться на то, чего для меня не существует. :3')
        TELEGRAM_BOT.value.register_next_step_handler(message, self.sub_next_step)

    def unsub(self, message):
        telegram_id = message.from_user.id
        markup = markups.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(markups.KeyboardButton('Течение'), markups.KeyboardButton('Борис'),
                   *[markups.KeyboardButton(target) for target in self._godnota],
                   markups.KeyboardButton('Закончить'))
        TELEGRAM_BOT.value.send_message(telegram_id, 'От чего хотите отписаться?', reply_markup=markup)
        TELEGRAM_BOT.value.register_next_step_handler(message, self.unsub_next_step)

    def unsub_next_step(self, message):
        telegram_id = message.from_user.id
        text = message.text
        if text == 'Течение':
            result = self._change_subscribers_list('flow', telegram_id, add=False)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы не будете получать обновления Течения')
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы не были подписаны на Течение')
        elif text == 'Борис':
            result = self._change_subscribers_list('boris', telegram_id, add=False)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы не будете получать обновления Бориса')
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы не были подписаны на Бориса')
        elif text in self._godnota:
            result = self._change_subscribers_list(self._godnota[text], telegram_id, add=False)
            if result:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Теперь вы не будете получать обновления из ' + text)
            else:
                TELEGRAM_BOT.value.send_message(telegram_id, 'Вы не были подписаны на ' + text)
        elif text == 'Закончить':
            markup = markups.ReplyKeyboardRemove(selective=False)
            TELEGRAM_BOT.value.send_message(message.from_user.id, 'Рад услужить', reply_markup=markup)
            return
        else:
            TELEGRAM_BOT.value.send_message(telegram_id, 'Нельзя отписаться от того, чего не существует для меня. :3')
        TELEGRAM_BOT.value.register_next_step_handler(message, self.unsub_next_step)

    def _send_image_message(self, post: DiffPost, link: str) -> None:
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился фото в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(post.user.username, post.title, post.description, link)
        for addressee in self._last_updates['flow']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_text_message(self, post: DiffPost, link: str) -> None:
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился мыслями в Течении:_' \
                   '\n*{}*\n{}\n{}'
        message = template.format(post.user.username, post.title, post.description, link)
        for addressee in self._last_updates['flow']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_audio_message(self, post: DiffPost, link: str) -> None:
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился аудиозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(post.user.username, post.title, post.description, link)
        for addressee in self._last_updates['flow']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_video_message(self, post: DiffPost, link: str) -> None:
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился видеозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(post.user.username, post.title, post.description, link)
        for addressee in self._last_updates['flow']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_other_message(self, post: DiffPost, link: str) -> None:
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился чем-то неординарным в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(post.user.username, post.title, post.description, link)
        for addressee in self._last_updates['flow']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_boris_message(self, *comments):
        with_files = False
        author = comments[0].user.username
        text = []
        for comment in comments:
            if comment.files:
                with_files = True
            if comment.text:
                text.append(comment.text)
        text = '\n\n_и продолжает:_\n\n'.join(text)
        template = '_Скрывающийся под псевдонимом_ *~{}* _вот что пишет Борису:_' \
                   '\n\n{}{}\n{}'
        link = self._api.url + 'boris'
        if with_files:
            with_files = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        else:
            with_files = ''
        message = template.format(author, text, with_files, link)
        for addressee in self._last_updates['boris']['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def _send_godnota_message(self, title: str, node: int) -> None:
        template = '_В коллекции_ *{}* _появилось что-то новенькое_'
        link = self._api.post_url.format(node)
        message = template.format(title, link)
        for addressee in self._last_updates['comments'][node]['subscribers']:
            TELEGRAM_BOT.value.send_message(addressee, message, parse_mode='Markdown')

    def scheduled(self):
        post_types: Dict[str, Callable[[DiffPost, str], None]] = {'image': self._send_image_message,
                                                                  'text': self._send_text_message,
                                                                  'audio': self._send_audio_message,
                                                                  'video': self._send_video_message,
                                                                  'other': self._send_other_message}
        self._check_updates()
        while self._flow_messages:
            post = self._flow_messages.pop()
            if post.type in post_types:
                link = self._api.post_url.format(post.id)
                post_types[post.type](post, link)
        while self._boris_messages:
            comments = [self._boris_messages.pop()]
            while self._boris_messages and self._boris_messages[-1].user.username == comments[0].user.username:
                comments.append(self._boris_messages.pop())
            self._send_boris_message(*comments)
        while self._godnota_updates:
            title = self._godnota_updates.pop()
            node = self._godnota[title]
            self._send_godnota_message(title, node)


vault = Vault(VAULT_TEST)

__all__ = ['vault']
