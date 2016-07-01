"""This module handles spectrum data objects."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
logging.basicConfig(level=logging.INFO)
from collections import Counter

from specutils.core.generic import GenericSpectrum1D

from astropy.nddata import NDData, NDArithmeticMixin, NDIOMixin
import numpy as np
from astropy.units import Quantity, Unit


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
        data_dict = {'id': id, 'spec1d_path': spec1d_path,
                     'spec2d_path': spec2d_path, 'image_path': image_path}

        data_dict.update(kwargs)

        self._collection.append(data_dict)

    def load(self, index):
        item = self.collection[index]

        spectrum1d = MOSSpectrum1D.read(item['spec1d_path'], format='spectrum1d')
        spectrum2d = MOSSpectrum2D.read(item['spec2d_path'], format='spectrum2d')
        image = MOSImage.read(item['image_path'], format='mos-image')

        new_item = {}
        new_item.update(item)
        new_item.update({'spec1d': spectrum1d, 'spec2d': spectrum2d,
                         'image': image, 'id': item['id']})

        return new_item

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self.load(i) for i in
                    range(key.start, key.stop, key.step)]
        return self.load(key)


class BaseMOS2D(NDIOMixin, NDArithmeticMixin, NDData):
    """
    Base base class image data.
    """
    def __init__(self, name, *args, **kwargs):
        super(BaseMOS2D, self).__init__(*args, **kwargs)
        self._name = name
        self._dispersion_unit = None
        self._cross_dispersion_unit = None

    @property
    def data(self):
        """Flux quantity with mask applied. Returns a masked array
        containing a Quantity object."""
        data = np.ma.array(
            Quantity(self._data, unit=self.unit),
            mask=self.mask)

        return data

    @property
    def dispersion_unit(self):
        if self._dispersion_unit is None:
            try:
                self._dispersion_unit = self.wcs.wcs.cunit[0]
            except:
                self._dispersion_unit = Unit("")

        return self._dispersion_unit

    @property
    def cross_dispersion_unit(self):
        if self._cross_dispersion_unit is None:
            try:
                self._cross_dispersion_unit = self.wcs.wcs.cunit[1]
            except:
                self._cross_dispersion_unit = Unit("")

        return self._cross_dispersion_unit


class MOSImage(BaseMOS2D):
    """
    Base base class image data.
    """
    def __init__(self, *args, **kwargs):
        super(MOSImage, self).__init__(*args, **kwargs)


class MOSSpectrum2D(BaseMOS2D):
    """
    Base base class image data.
    """
    def __init__(self, *args, **kwargs):
        super(MOSSpectrum2D, self).__init__(*args, **kwargs)


class MOSSpectrum1D(GenericSpectrum1D):
    """
    Class for 1d spectral data.
    """
    def __init__(self, *args, **kwargs):
        super(MOSSpectrum1D, self).__init__(*args, **kwargs)

    @property
    def data(self):
        """Flux quantity with mask applied. Returns a masked array
        containing a Quantity object."""
        data = np.ma.array(
            Quantity(self._data, unit=self.unit),
            mask=self.mask)

        return data

    @property
    def dispersion_unit(self):
        if self._dispersion_unit is None:
            try:
                self._dispersion_unit = self.wcs.wcs.cunit[0]
            except:
                self._dispersion_unit = Unit("")

        return self._dispersion_unit
