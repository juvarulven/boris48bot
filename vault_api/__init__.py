from .types import Stats, Comments, Diff, User, Node, Tag
import log
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
        self._diff_url = url + 'node/diff'
        self._comments_url = url + 'node/{}/comment'
        self._related_url = url + 'node/{}/related'
        self.boris_node = 696

    def get_stats(self):
        try:
            return Stats(get_json(self._stats_url))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить stats Убежища: ' + str(error)
            log.log(error_message)

    def get_diff(self, start=None, end=None, with_heroes=False,
                 with_updated=False, with_recent=False, with_valid=False):
        params = {'start': start,
                  'end': end,
                  'with_heroes': with_heroes,
                  'with_updated': with_updated,
                  'with_recent': with_recent,
                  'with_valid': with_valid}
        try:
            return Diff(get_json(self._diff_url, params=params))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить diff Убежища: ' + str(error)
            log.log(error_message)

    def get_recent(self):
        response = self.get_diff(with_recent=True)
        return response.recent

    def get_heroes(self):
        response = self.get_diff(with_heroes=True)
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
        node_names_and_ids = {'Хорошей музыки тред': 1691}
        try:
            response = get_json(self._related_url)['related']['albums']['/годнота']
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить related Убежища' + str(error)
            log.log(error_message)
            return
        for node in response:
            node_names_and_ids[node['title']] = node['id']
        return node_names_and_ids

    def get_node(self, node):
        try:
            return Node(get_json(self._node_url.format(node)))
        except Exception as error:
            error_message = 'vault_api: Ошибка при попытке получить node Убежища: ' + str(error)
            log.log(error_message)




def get_json(url, **params):
    response = requests.get(url, **params)
    if requests.status_codes == 200:
        return response.json()
