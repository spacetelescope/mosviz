from __future__ import absolute_import, division, print_function

from glue.config import data_factory


__all__ = ['mosviz_cutout_loader', 'mosviz_spectrum2d_loader','mosviz_spectrum1d_loader']

SPECTRUM1D_LOADERS = {}
SPECTRUM2D_LOADERS = {}
CUTOUT_LOADERS = {}


def mosviz_spectrum1d_loader(label, *args, **kwargs):

    adder = data_factory(label, *args, **kwargs)

    def wrapper(func):
        SPECTRUM1D_LOADERS[label] = func
        return adder(func)

    return wrapper


def mosviz_spectrum2d_loader(label, *args, **kwargs):

    adder = data_factory(label, *args, **kwargs)

    def wrapper(func):
        SPECTRUM2D_LOADERS[label] = func
        return adder(func)

    return wrapper


def mosviz_cutout_loader(label, *args, **kwargs):

    adder = data_factory(label, *args, **kwargs)

    def wrapper(func):
        CUTOUT_LOADERS[label] = func
        return adder(func)

    return wrapper

