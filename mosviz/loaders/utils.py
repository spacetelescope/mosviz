import re

from glue.config import data_factory

__all__ = ['mosviz_cutout_loader', 'mosviz_spectrum2d_loader',
           'mosviz_spectrum1d_loader', 'mosviz_level2_loader',
           'split_file_name']

SPECTRUM1D_LOADERS = {}
SPECTRUM2D_LOADERS = {}
CUTOUT_LOADERS = {}
LEVEL2_LOADERS = {}

FILENAME_REGEX = re.compile(r'^(.+)\[(\d+)\]$')


def split_file_name(file_name, default_ext=0):
    """
    Used to split fits extension from file name.
    Extensions are appended to the file path in
    square brackets as follows:
        <file_path>[<extension>]
    If file_name doesn't have an extension,
    the function will set ext to 0 by default.

    Parameters
    ----------
    file_name : str
        File name to parse
    default_ext : int
        Default extension number if file name
        doesnt have extension number.

    Returns
    -------
    path_and_ext : list

    """

    match = FILENAME_REGEX.match(file_name)

    if match is None:
        return [file_name, default_ext]

    groups = list(match.groups())
    if groups[1].isnumeric():
        groups[1] = int(groups[1])
    return groups


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


def mosviz_level2_loader(label, *args, **kwargs):

    adder = data_factory(label, *args, **kwargs)

    def wrapper(func):
        LEVEL2_LOADERS[label] = func
        return adder(func)

    return wrapper

