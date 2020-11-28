from . import types
from .types import Stats, Comments, Diff, User, Node, Tag
from utils import log
import requests
import datetime

TEST_URL = 'https://pig.staging.vault48.org/'
MAIN_URL = 'https://pig.vault48.org/'


class Api:
    def __init__(self, testing=False):
        # Backend urls (example: https://pig.staging.vault48.org/node/696)
        self._url = TEST_URL if testing else MAIN_URL
        self._stats_url = self._url + 'stats/'
        self._node_url = self._url + 'node/{}'
        self._diff_url = self._url + 'flow/diff'
        self._comments_url = self._url + 'node/{}/comment'
        self._related_url = self._url + 'node/{}/related'
        self._tags_url = self._url + 'tag/nodes'

        # Frontend urls (example: https://staging.vault48.org/post696)
        self.url = self._url[:8] + self._url[12:]
        self.post_url = self._url + 'post{}'
        self.boris_node = 696
        types.URL = self._url + 'static/'  # Forward backend static url in types

    def get_stats(self):
        try:
            return Stats(get_json(self._stats_url))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить stats Убежища: ' + str(error)
            log.log(error_message)

    def get_diff(self, start=None, end=None, with_heroes=False,
                 with_updated=False, with_recent=False, with_valid=False):
        if start is None or end is None:
            time = datetime.datetime.utcnow().isoformat(timespec='milliseconds')[:-1] + 'Z'
            start = time
            end = time
        params = {'start': start,
                  'end': end,
                  'with_heroes': str(with_heroes).lower(),
                  'with_updated': str(with_updated).lower(),
                  'with_recent': str(with_recent).lower(),
                  'with_valid': str(with_valid).lower()}
        try:
            return Diff(get_json(self._diff_url, params=params))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить diff Убежища: ' + str(error)
            log.log(error_message)

    def get_recent(self):
        response = self.get_diff(with_recent=True)
        if response:
            return response.recent

    def get_heroes(self):
        response = self.get_diff(with_heroes=True)
        if response:
            return response.heroes

    def get_comments(self, node, take, skip=0):
        params = {'take': take,
                  'skip': skip}
        try:
            return Comments(get_json(self._comments_url.format(node), params=params))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить comments Убежища: ' + str(error)
            log.log(error_message)

    def get_boris(self, take, skip=0):
        return self.get_comments(self.boris_node, take, skip)

    def get_godnota(self):
        params = {'name': '/годнота',
                  'offset': 0,
                  'limit': 25}
        try:
            response = get_json(self._tags_url, params=params)
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить годноту Убежища' + str(error)
            log.log(error_message)
            return
        nodes = response['nodes']
        return {node['title']: node['id'] for node in nodes}

    def get_node(self, node):
        try:
            return Node(get_json(self._node_url.format(node)))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить node Убежища: ' + str(error)
            log.log(error_message)


def get_json(url, **params):
    response = requests.get(url, **params)
    if response.ok:
        return response.json()
