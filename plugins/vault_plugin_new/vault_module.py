from vault_api import Api
from vault_api.types import VaultApiException, Comment, DiffPost
from .plugin_types import VaultPluginException, VaultCommentsBlock, VaultImagePost, VaultTextPost, VaultAudioPost
from .plugin_types import VaultVideoPost, VaultOtherPost, VaultGodnotaPost, VaultUpdates
from typing import Callable, Any, Tuple, Iterator, List, Union, Dict


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

    def get_comments(self, node_id: str, number=10) -> List[VaultCommentsBlock]:
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
        return [comment for comment in self._build_comment_list_item(comment_objects_list, post_url)]

    def _build_comment_list_item(self, comments_list: List[Comment], post_url) -> Iterator[VaultCommentsBlock]:
        while comments_list:
            comment = comments_list.pop()
            username = comment.user.username
            user_url = self._generate_user_url(username)
            with_file = [bool(comment.files)]
            user_comments = [comment.text]
            timestamp = comment.created_at
            while comments_list and username == comments_list[-1].user.username:
                comment = comments_list.pop()
                user_comments.append(comment.text)
                with_file.append(bool(comment.files))
            yield VaultCommentsBlock(username, user_url, user_comments, any(with_file), post_url, timestamp)

    def _generate_user_url(self, username: str) -> str:
        return self._api.url + '~' + username

    def check_updates(self, flow_timestamp, boris_timestamp, godnota_nodes: Dict[str, str]) -> VaultUpdates:
        flow_current_timestamp, boris_current_timestamp = self.get_flow_and_boris_timestamps()
        diff = self._api.get_diff(flow_timestamp, flow_timestamp, with_recent=True)
        recent = diff.recent
        flow_posts = []
        if flow_timestamp < flow_current_timestamp:
            new_posts = diff.before
            while new_posts:
                flow_posts.append(self._make_flow_post_object(new_posts.pop()))
        boris_posts = []
        if boris_timestamp < boris_current_timestamp:
            new_comments = self.get_comments(self._api.boris_node)
            new_comments = [comment for comment in new_comments if comment.timestamp > boris_timestamp]
            while new_comments:
                boris_posts.append(new_comments.pop())
        godnota_posts = []
        for recent_node in recent:
            node_id = str(recent_node.id)
            if node_id in godnota_nodes and godnota_nodes[node_id] < recent_node.commented_at:




    def _make_flow_post_object(self, diff_post: DiffPost) -> Union[VaultTextPost, VaultImagePost, VaultAudioPost,
                                                                   VaultVideoPost, VaultOtherPost]:
        post_type = diff_post.type
        username = diff_post.user.username
        user_url = self._generate_user_url(username)
        post_url = self._api.post_url.format(diff_post.id)
        if post_type == 'text':
            return VaultTextPost(username, user_url, diff_post.title,
                                 post_url, diff_post.description)
        elif post_type == 'image':
            return VaultImagePost(username, user_url, diff_post.title,
                                  post_url, diff_post.thumbnail, diff_post.description)
        elif post_type == 'audio':
            return VaultAudioPost(username, user_url, post_url)
        elif post_type == 'video':
            return VaultVideoPost(username, user_url, post_url)
        elif post_type == 'other':
            return VaultOtherPost(username, user_url, post_url)
