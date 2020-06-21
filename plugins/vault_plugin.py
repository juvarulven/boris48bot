from typing import Optional, Dict, Tuple
from telebot import types as markups
from database import Database
from vault_api import Api
import log
from global_variables import RUNNING_FLAG


class Vault:
    def __init__(self):
        self._api = Api(testing=True)
        self._flow_messages = []
        self._boris_messages = []
        self._godnota_messages = {}
        self._db = Database('vault_plugin')
        self._last_updates = {'flow': {'timestamp': None, 'subscribers': []},
                              'boris': {'timestamp': None, 'subscribers': []},
                              'comments': {}, 'comments_count': None}
        self._godnota = None
        self._init_database()

    @staticmethod
    def _do_it_5_times(what_to_do, *args, **kwargs):
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

    def _init_database(self):
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
            self._last_updates = last_updates
        self._godnota = self._do_it_5_times(self._api.get_godnota)
        if self._godnota is None:
            log.log('vault_plugin: Не удалось получить годноту за пять попыток')
            return
        for title, post_id in self._godnota:
            if post_id not in self._last_updates['comments']:
                need_update_db = True
                comments = self._do_it_5_times(self._api.get_comments, post_id, 1)
                if comments is None:
                    log.log('vault_plugin: не удалось получить комментарии из {} за пять попыток'.format(title))
                    return
                self._last_updates['comments'][post_id] = {}
                self._last_updates['comments'][post_id]['title'] = title
                self._last_updates['comments'][post_id]['timestamp'] = comments.comments[0].created_at
                self._last_updates['comments'][post_id]['subscribers'] = {}
        if need_update_db:
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()

    def _change_subscribers_list(self, target, telegram_id, add):
        need_update_db = False
        if target in self._last_updates:
            target = self._last_updates[target]['subscribers']
            if telegram_id not in target:
                need_update_db = True
                if add:
                    target.append(telegram_id)
                else:
                    target.remove(telegram_id)
        elif target in self._last_updates['comments']:
            target = self._last_updates['comments'][target]['subscribers']
            if telegram_id not in target:
                need_update_db = True
                if add:
                    target.append(telegram_id)
                else:
                    target.remove(telegram_id)
        else:
            raise AssertionError('vault_plugin: ' + str(target) + 'отсутствует в базе')
        if need_update_db:
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()
        return need_update_db

    def _check_updates(self):
        stats = self._api.get_stats()
        need_update_db = []
        if stats is not None:
            need_update_db = [self._update_flow(stats.timestamps_flow),
                              self._update_boris(stats.timestamps_boris, stats.comments_total)]
        need_update_db.append(self._update_godnota(stats.comments_total))
        if stats.comments_total != self._last_updates['comments_count']:
            self._last_updates['comments_count'] = stats.comments_total
            need_update_db.append(True)
        if any(need_update_db):
            self._db.update_document('last_updates', fields_with_content=self._last_updates)
            self._db.save_and_update()

    def _update_flow(self, current_timestamp):
        last_timestamp = self._last_updates['flow']['timestamp']
        if last_timestamp < current_timestamp:
            diff = self._api.get_diff(last_timestamp, last_timestamp)
            if diff is None:
                return False
            self._last_updates['flow']['timestamp'] = current_timestamp
            self._flow_messages = diff.before
            return True
        return False

    def _update_boris(self, current_timestamp, current_comments_count):
        last_timestamp = self._last_updates['boris']['timestamp']
        comments_count = current_comments_count - self._last_updates['comments_count'] + 5
        if last_timestamp < current_timestamp:
            comments = self._update_comments(self._api.boris_node, last_timestamp, comments_count)
            if not comments:
                return False
            self._last_updates['boris']['timestamp'] = current_timestamp
            return True
        return False

    def _update_comments(self, node, last_timestamp, comments_count):
        comments_list = []
        comments = self._api.get_comments(node, comments_count)
        if comments is None:
            return comments_list
        for comment in comments.comments:
            if comment.created_at <= last_timestamp:
                break
            comments_list.append(comment)
        return comments_list

    def _update_godnota(self, current_comments_count):
        need_update_db = False
        recent = self._api.get_recent()
        if recent is None:
            return False
        comments_count = current_comments_count - self._last_updates['comments_count'] + 5
        for node in recent:
            node_id = node.id
            current_timestamp = node.commented_at
            if node_id in self._last_updates['comments']:
                node_dict = {}
                current = self._last_updates['comments'][node_id]
                last_timestamp = current['timestamp']
                if current['subscribers'] and current_timestamp > last_timestamp:
                    comments = self._update_comments(node_id, last_timestamp, comments_count)
                    if not comments:
                        continue
                    need_update_db = True
                    current['timestamp'] = current_timestamp
                    node_dict['title'] = node.title
                    node_dict['comments_list'] = comments
                    self._godnota_messages[node_id] = node_dict
        return need_update_db

    def sub(self, bot, message):
        telegram_id = message.from_user.id
        text = message.text
        if len(text) < 6:
            markup = markups.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(markups.KeyboardButton('/sub Течение'), markups.KeyboardButton('/sub Борис'),
                       *[markups.KeyboardButton('/sub ' + target) for target in self._godnota])
            bot.send_message(telegram_id, 'На что хотите подписаться?', reply_markup=markup)
        else:
            text = text[5:]
            if text == 'Teчение':
                result = self._change_subscribers_list('flow', telegram_id, add=True)
                if result:
                    bot.send_message(telegram_id, 'Теперь вы будете получать обновления Течения')
                else:
                    bot.send_message(telegram_id, 'Вы уже подписаны на Течение')
            elif text == 'Борис':
                result = self._change_subscribers_list('flow', telegram_id, add=True)
                if result:
                    bot.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
                else:
                    bot.send_message(telegram_id, 'Вы уже подписаны на Бориса')
            elif text in self._godnota:
                result = self._change_subscribers_list(self._godnota[text], telegram_id, add=True)
                if result:
                    bot.send_message(telegram_id, 'Теперь вы будете получать обновления из ' + text)
                else:
                    bot.send_message(telegram_id, 'Вы уже подписаны на ' + text)
            else:
                bot.send_message(telegram_id, 'На такое невозможно подписаться')

    def subscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._add_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Теперь вы будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы уже подписаны на Бориса')

    def unsubscribe_flow(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._delete_subscriber('flow', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Течения')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Течение')

    def unsubscribe_boris(self, bot, message):
        telegram_id = message.from_user.id
        added_subscriber = self._delete_subscriber('boris', telegram_id)
        if added_subscriber:
            bot.send_message(telegram_id, 'Вы больше не будете получать обновления Бориса')
        else:
            bot.send_message(telegram_id, 'Вы не были подписаны на Бориса')

    def _send_image_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился фото в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_text_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился мыслями в Течении:_' \
                   '\n*{}*\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_audio_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился аудиозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_video_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился видеозаписью в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_other_message(self, bot, author, title, description, link):
        template = '_Скрывающийся под псевдонимом_ *~{}* _поделился чем-то неординарным в Течении:_' \
                   '\n*{}*\n_и написал:_\n{}\n{}'
        message = template.format(author, title, description, link)
        for addressee in self._subscribers['flow']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def _send_boris_message(self, bot, author, comment, with_files):
        template = '_Скрывающийся под псевдонимом_ *~{}* _вот что пишет Борису:_' \
                   '\n{}{}\n{}'
        link = self._api.url + 'boris'
        if with_files:
            with_files = '\n\n_да вдобавок прикрепляет какие-то прикрепления!_'
        else:
            with_files = ''
        message = template.format(author, comment, with_files, link)
        for addressee in self._subscribers['boris']:
            bot.send_message(addressee, message, parse_mode='Markdown')

    def scheduled(self, bot):
        self._check_updates()
        while self._flow_messages:
            post = self._flow_messages.pop()
            author = post['user']['username']
            title = post['title']
            description = post['description']
            link = '{}post{}'.format(self._api.url, post['id'])
            content_type = post['type']
            if content_type == 'image':
                self._send_image_message(bot, author, title, description, link)
            if content_type == 'text':
                self._send_text_message(bot, author, title, description, link)
            if content_type == 'audio':
                self._send_audio_message(bot, author, title, description, link)
            if content_type == 'video':
                self._send_video_message(bot, author, title, description, link)
            if content_type == 'other':
                self._send_other_message(bot, author, title, description, link)
        while self._boris_messages:
            with_files = False
            comment = self._boris_messages.pop()
            author = comment['user']['username']
            text = comment['text']
            if comment['files']:
                with_files = True
            while self._boris_messages and self._boris_messages[-1]['user']['username'] == author:
                comment = self._boris_messages.pop()
                text += '\n_и продолжает:_\n'
                text += comment['text']
                if comment['files']:
                    with_files = True
            self._send_boris_message(bot, author, text, with_files)


vault = Vault()

__all__ = ['vault']
