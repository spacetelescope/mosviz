from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from functools import wraps

import astropy.io.registry as io_registry


def data_loader(label, identifier, data_class, priority=-1, **kwargs):
    """
    A decorator that registers a function and identifies with an Astropy io
    registry object.

    Parameters
    ----------
    func : function
        Function added to the registry in order to read data files.
    """
    def decorator(func):
        logging.info("Added {} to loader registry.".format(label))

        func.loader_wrapper = True

        format = label #"-".join(label.lower().split())
        io_registry.register_reader(format, data_class, func)
        io_registry.register_identifier(format, data_class, identifier)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return decorator
