"""This module handles spectrum data objects."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
logging.basicConfig(level=logging.INFO)

from specutils.core.generic import GenericSpectrum1D

from astropy.nddata import NDData, NDArithmeticMixin, NDIOMixin


class MOSData(NDIOMixin):
    """
    Core data container for MOS data.
    """
    def __init__(self, name, **kwargs):
        self._name = name
        self._collection = []

    @property
    def name(self):
        return self._name

    @property
    def collection(self):
        return self._collection

    def add(self, id, spec1d_path, spec2d_path, image_path, **kwargs):
        data_dict = {'id': id, 'spec1d': spec1d_path, 'spec2d': spec2d_path,
                     'image': image_path}

        data_dict.update(kwargs)

        self._collection.append(data_dict)

    def load(self, index):
        item = self.collection[index]

        spectrum1d = GenericSpectrum1D.read(item['spec1d'],
                                            format='spectrum1d')
        spectrum2d = Spectrum2D.read(item['spec2d'], format='spectrum2d')
        image = Image.read(item['image'], format='mos-image')

        # item.update({'spec1d': spectrum1d, 'spec2d':
        #     spectrum2d, 'image': image})

        return {'spec1d': spectrum1d, 'spec2d':
                spectrum2d, 'image': image, 'id': item['id']}

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self.load(i) for i in
                    range(key.start, key.stop, key.step)]
        return self.load(key)


class Image(NDIOMixin, NDArithmeticMixin, NDData):
    """
    Base base class image data.
    """
    def __init__(self, name, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self._name = name


class Spectrum2D(GenericSpectrum1D):
    """
    Base base class image data.
    """
    def __init__(self, *args, **kwargs):
        super(Spectrum2D, self).__init__(*args, **kwargs)

