from glue.config import data_factory


__all__ = ['mosviz_cutout_loader', 'mosviz_spectrum2d_loader',
           'mosviz_spectrum1d_loader', 'mosviz_level2_loader',
           'split_file_name']

SPECTRUM1D_LOADERS = {}
SPECTRUM2D_LOADERS = {}
CUTOUT_LOADERS = {}
LEVEL2_LOADERS = {}


def split_file_name(file_name):
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

    Returns
    -------
    path_and_ext : list

    """
    path = file_name
    ext = 0

    has_ext = "[" in file_name and "]" in file_name

    if has_ext:
        if file_name.count("[") > 1 or file_name.count("]") > 1:
            raise Exception("File path contains multiple brackets")

        path = file_name[:file_name.find("[")]
        ext = file_name[file_name.find("[")+1:file_name.find("]")]
        if ext.isnumeric():
            ext = int(ext)

    return [path, ext]


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

