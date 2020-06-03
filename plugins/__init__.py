from . import test_plugin

plugins = [{'handler': test_plugin.test_simple, 'commands': ['test']}]
scheduled_plugins = [{'handler': test_plugin.test_scheduled, 'minutes': 1}]

__all__ = ['plugins', 'scheduled_plugins']
