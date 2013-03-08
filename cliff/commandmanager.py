"""Discover and lookup command plugins.
"""

import logging

import pkg_resources


LOG = logging.getLogger(__name__)


class EntryPointWrapper(object):
    """Wrap up a command class already imported to make it look like a plugin.
    """

    def __init__(self, name, command_class):
        self.name = name
        self.command_class = command_class

    def load(self):
        return self.command_class


class CommandManager(object):
    """Discovers commands and handles lookup based on argv data.

    :param namespace: String containing the setuptools entrypoint namespace
                      for the plugins to be loaded. For example,
                      ``'cliff.formatter.list'``.
    :param convert_underscores: Whether cliff should convert underscores to
                                to spaces in entry_point commands.
    """
    def __init__(self, namespace, convert_underscores=True):
        self.commands = {}
        self.namespace = namespace
        self.convert_underscores = convert_underscores
        self._load_commands()

    def _load_commands(self):
        for ep in pkg_resources.iter_entry_points(self.namespace):
            LOG.debug('found command %r', ep.name)
            cmd_name = ep.name.replace('_', ' ') if self.convert_underscores else ep.name
            self.commands[cmd_name] = ep
        return

    def __iter__(self):
        return iter(self.commands.items())

    def add_command(self, name, command_class):
        self.commands[name] = EntryPointWrapper(name, command_class)

    def find_command(self, argv):
        """Given an argument list, find a command and
        return the processor and any remaining arguments.
        """
        search_args = argv[:]
        name = ''
        while search_args:
            if search_args[0].startswith('-'):
                raise ValueError('Invalid command %r' % search_args[0])
            next_val = search_args.pop(0)
            name = '%s %s' % (name, next_val) if name else next_val
            if name in self.commands:
                cmd_ep = self.commands[name]
                cmd_factory = cmd_ep.load()
                return (cmd_factory, name, search_args)
        else:
            raise ValueError('Unknown command %r' %
                             (argv,))
