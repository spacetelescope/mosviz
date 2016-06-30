"""This module handles spectrum data objects."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import logging
logging.basicConfig(level=logging.INFO)
import re

# THIRD-PARTY
import numpy as np
from astropy.units import Quantity, spectral_density, spectral
from specutils.core.generic import GenericSpectrum1D

from astropy.nddata import NDData, NDArithmeticMixin, NDIOMixin


class MOSData(NDIOMixin):
    """
    Core data container for MOS data.
    """
    def __init__(self, spectrum1d, spectrum2d, image, **kwargs):
        self._spectrum1d = GenericSpectrum1D.read(spectrum1d)
        self._spectrum2d = Spectrum2D.read(spectrum2d)
        self._image = Image.read(image)

    @property
    def spectrum1d(self):
        return self._spectrum1d

    @property
    def spectrum2d(self):
        return self._spectrum2d

    @property
    def image(self):
        return self._image


class Image(NDIOMixin, NDArithmeticMixin, NDData):
    """
    Base base class image data.
    """
    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)


class Spectrum2D(GenericSpectrum1D):
    """
    Base base class image data.
    """
    def __init__(self, *args, **kwargs):
        super(Spectrum2D, self).__init__(*args, **kwargs)

