from . import test_plugin
from . import help_plugin

plugins = [{'commands': ['start'], 'handler': help_plugin.start_message, 'help': 'присылаю приветствие'},
           {'commands': ['help'], 'handler': help_plugin.help_message, 'help': 'присылаю справку по командам'},
           {'commands': ['test'], 'handler': test_plugin.test_simple, 'help': 'отвечаю "passed!"'}]

scheduled_plugins = [{'handler': test_plugin.test_scheduled, 'minutes': 1}]

__all__ = ['plugins', 'scheduled_plugins']
