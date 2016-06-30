from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os, sys
import importlib
import inspect


class Registry(object):
    """
    Maintains a set of referential objects.
    """
    def __init__(self):
        self._members = []

    @property
    def members(self):
        return self._members


class PluginRegistry(Registry):
    """Loads and stores custom plugins."""
    def __init__(self):
        super(PluginRegistry, self).__init__()
        self.load()

    def load(self):
        """
        Load plugins.
        """
        cur_path = os.path.abspath(os.path.join(__file__, '..', '..',
                                                'plugins'))
        usr_path = os.path.join(os.path.expanduser('~'), '.mosviz')

        # This order determines priority in case of duplicates; paths higher
        # in this list take precedence
        check_paths = [usr_path, cur_path]

        if not os.path.exists(usr_path):
            os.mkdir(usr_path)

        for path in check_paths:
            for mod in [x for x in os.listdir(path) if x.endswith('.py')]:
                mod = mod.split('.')[0]
                mod = importlib.import_module('mosviz.plugins.' + str(mod))
                cls_members = inspect.getmembers(
                    mod, lambda member: inspect.isclass(member)
                                        and 'Plugin' in [x.__name__
                                                         for x in
                                                         member.__bases__])

                for cls_name, cls_plugin in cls_members:
                    self._members.append(cls_plugin())


class LoaderRegistry(Registry):
    """
    This registry is responsible for searching for and importing custom data
    loaders.
    """
    def __init__(self):
        super(LoaderRegistry, self).__init__()
        self.load_py()

    @staticmethod
    def load_py():
        """
        Loads python files as custom loaders.
        """
        cur_path = os.path.abspath(os.path.join(__file__, '..', '..', 'io',
                                                'loaders'))
        usr_path = os.path.join(os.path.expanduser('~'), '.mosviz')

        # This order determines priority in case of duplicates; paths higher
        # in this list take precedence
        check_paths = [usr_path, cur_path]

        if not os.path.exists(usr_path):
            os.mkdir(usr_path)

        for path in check_paths:
            for mod in [x for x in os.listdir(path) if x.endswith('.py')]:
                mod = mod.split('.')[0]
                sys.path.insert(0, cur_path)
                mod = importlib.import_module(str(mod))
                members = inspect.getmembers(mod, predicate=inspect.isfunction)

                sys.path.pop(0)


# Create loader registry instance
loader_registry = LoaderRegistry()
plugin_registry = PluginRegistry()
