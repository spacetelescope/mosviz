from __future__ import absolute_import, division, print_function

from glue.config import data_factory
from glue.core import Data
from glue.core.coordinates import coordinates_from_header
from astropy.io import fits
import numpy as np


@data_factory('NIRSpec 1D Spectrum')
def nirspec_spectrum1d_reader(file_name):
    """
    Data loader for MOSViz 1D spectrum.

    This function extracts the DATA, QUALITY, and VAR
    extensions and returns them as a glue Data object.

    It then uses the header keywords of the DATA extension
    to detemine the wavelengths.
    """

    hdulist = fits.open(file_name)

    # make wavelength a seperate component in addition to coordinate
    # so you can plot it on the x axis
    wavelength = np.linspace(hdulist['DATA'].header['CRVAL1'],
        hdulist['DATA'].header['CRVAL1']*hdulist['DATA'].header['CDELT1'],
        hdulist['DATA'].header['NAXIS1'])[::-1]

    data = Data(label='1D Spectrum')
    data.coords = coordinates_from_header(hdulist[1].header)
    data.add_component(wavelength, 'Composed Wavelength')
    data.add_component(hdulist['DATA'].data, 'Spectral Flux')
    data.add_component(hdulist['VAR'].data, 'Variance')
    data.add_component(hdulist['QUALITY'].data, 'Data Quality')

    return data


@data_factory('NIRSpec 2D Spectrum')
def nirspec_spectrum2d_reader(file_name):
    """
    Data loader for simulated NIRSpec 2D spectrum.

    This function extracts the DATA, QUALITY, and VAR
    extensions and returns them as a glue Data object.

    It then uses the header keywords of the DATA extension
    to detemine the wavelengths.
    """

    hdulist = fits.open(file_name)
    data = Data(label='2D Spectrum')
    data.coords = coordinates_from_header(hdulist[1].header)
    data.add_component(hdulist['DATA'].data, 'Spectral Flux')
    data.add_component(hdulist['VAR'].data, 'Variance')
    data.add_component(hdulist['QUALITY'].data, 'Data Quality')

    return data