from typing import Dict, List, Union, Optional
from .types import Stats, DiffPost, Hero, Comments, Diff, User, Node, Tag, VaultApiException
from utils import log
import requests

TEST_URL = 'https://staging.vault48.org:3334/'
MAIN_URL = 'https://vault48.org:3333/'


class Api:
    def __init__(self, testing=False):
        if testing:
            url = TEST_URL
        else:
            url = MAIN_URL
        self.url = url[:-6] + '/'
        self._stats_url = url + 'stats'
        self._node_url = url + 'node/{}'
        self.post_url = url + 'post{}'
        self._diff_url = url + 'node/diff'
        self._comments_url = url + 'node/{}/comment'
        self._related_url = url + 'node/{}/related'
        self.boris_node = 696

    def get_stats(self) -> Stats:
        """
        Получает /stats Убежища

        :return: Stats объект или None в случае провала
        """
        return Stats(get_json(self._stats_url))

    def get_diff(self, start="", end="", with_heroes=False, with_updated=False,
                 with_recent=False, with_valid=False) -> Diff:
        """
        Получает /node/diff Убежища. Если start и end пусты -- поля before и after будут пусты

        :param start: таймстамп формата 'YYYY-MM-DDTHH:MM:SS.uuuZ'
        :param end: таймстамп формата 'YYYY-MM-DDTHH:MM:SS.uuuZ'
        :param with_heroes:
        :param with_updated:
        :param with_recent:
        :param with_valid:
        :return: Diff объект или None в случае провала
        """
        params = {'start': start,
                  'end': end,
                  'with_heroes': str(with_heroes).lower(),
                  'with_updated': str(with_updated).lower(),
                  'with_recent': str(with_recent).lower(),
                  'with_valid': str(with_valid).lower()}
        return Diff(get_json(self._diff_url, params=params))

    def get_recent(self) -> List[DiffPost]:
        """
        Возвращает список из поля Diff.recent

        :return: список DiffPost объектов или None в случае неудачи
        """
        response = self.get_diff(with_recent=True)
        return response.recent

    def get_heroes(self) -> List[Hero]:
        """
        Возвращает список из поля Diff.heroes

        :return: список Hero объектов
        """
        response = self.get_diff(with_heroes=True)
        return response.heroes

    def get_comments(self, node: Union[str, int], take: Union[str, int], skip=0) -> Comments:
        """
        Получает /node/[node_id]/comment

        :param node: id ноды
        :param take: сколько взять
        :param skip: сколько пропустить
        :return: Comments объект
        """
        params = {'take': take,
                  'skip': skip}
        return Comments(get_json(self._comments_url.format(node), params=params))

    def get_boris(self, take: Union[int, str], skip=0) -> Comments:
        """
        Возвращает комментарии Бориса

        :param take: сколько получить
        :param skip: сколько пропустить
        :return: Comments объект
        """
        return self.get_comments(self.boris_node, take, skip)

    def get_godnota(self) -> Dict[str, int]:
        """
        Возвращает словарь нод, составленный из ответа Убежища через поиск по тегу '/годнота'

        :return: словарь вида {'title': node_id...}
        """
        node_names_and_ids = {'Хорошей музыки тред': 1691}
        response = get_json(self._related_url.format(1691))['related']['albums']['/годнота']
        for node in response:
            node_names_and_ids[node['title']] = node['id']
        return node_names_and_ids

    def get_node(self, node: Union[int, str]) -> Node:
        """
        Получает /node/[node_id] Убежища

        :param node: id ноды
        :return: Node объект
        """
        return Node(get_json(self._node_url.format(node)))


def get_json(url: str, **params) -> dict:
    """
    Идет по ссылке и возвращает json ответ ввиде словаря

    :param url: интернет ссылка
    :param params: параметры
    :return:
    """
    response = requests.get(url, **params)
    if response.status_code == 200:
        return response.json()
    else:
        raise VaultApiException('{} returns status code {}'.format(url, response.status_code))
