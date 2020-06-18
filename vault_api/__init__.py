import log
import requests


class Api:
    def __init__(self, url, port):
        self._stats_url = '{}:{}/stats'.format(url, port)
        self._flow_url = '{}:{}/node/diff'.format(url, port)
        self._comments_url = '{}:{}/node/{}/comment'.format(url, port, '{}')
        self._comments_count = 0
        self._flow_timestamp = None
        self._comments_nodes = {'boris': [696, '']}
        self._timestamps_loaded = False

    def _get_stats(self):
        try:
            return get_json(self._stats_url)
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при попытке получить stats Убежища: ' + str(error)
            log.log(error_message)

    def _update_comments_count_and_timestamps(self):
        result_timestamps = {}
        json = self._get_stats()
        if json:
            timestamps = json['timestamps']
            flow_current_timestamp = timestamps['flow_last_post']
            if self._flow_timestamp is None or self._flow_timestamp < flow_current_timestamp:
                result_timestamps['flow'] = flow_current_timestamp
            boris_current_timestamp = timestamps['boris_last_comment']
            boris_timestamp = self._comments_nodes['boris'][1]
            if not boris_timestamp or boris_timestamp < boris_current_timestamp:
                result_timestamps['boris'] = boris_current_timestamp
            comments_count = json['comments']['total']
            if self._comments_count < comments_count:
                for key, value in self._comments_nodes.items():
                    if key == 'boris':
                        continue
                    node_id = value[0]
                    content = self._get_comments(node_id, 1)
                    result_timestamps[key] = content['comments']['0']['created_at']
            return comments_count, result_timestamps
        else:
            return 0, {}

    def _get_updates(self):
        pass

    def get_comments_count_and_timestamps(self):
        comments_count, timestamps = self._update_comments_count_and_timestamps()
        if comments_count:
            yield 'comments_count', comments_count
            for name, timestamp in timestamps.items():
                yield name, timestamp

    def set_comments_count_and_timestamps(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'comments_count':
                self._comments_count = value
            elif key == 'flow':
                self._flow_timestamp = value
            else:
                self._comments_nodes[key] = value

    def _get_diff(self, start=None, end=None, with_heroes=False, with_updated=False, with_recent=False, with_valid=False):
        params = {'start': start,
                  'end': end,
                  'with_heroes': with_heroes,
                  'with_updated': with_updated,
                  'with_recent': with_recent,
                  'with_valid': with_valid}
        try:
            return get_json(self._flow_url, params=params)
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при попытке получить diff Убежища: ' + str(error)
            log.log(error_message)

    def _get_comments(self, node, take, skip=0):
        params = {'take': take,
                  'skip': skip}
        try:
            return get_json(self._comments_url.format(node), params=params)
        except Exception as error:
            error_message = 'vault_plugin: Ошибка при попытке получить comments Убежища: ' + str(error)
            log.log(error_message)


def get_json(url, **params):
    response = requests.get(url, **params)
    if requests.status_codes == 200:
        return response.json()
