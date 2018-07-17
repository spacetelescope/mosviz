import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from glue.core import Data
from glue.core.coordinates import coordinates_from_wcs

from .utils import mosviz_spectrum1d_loader, mosviz_spectrum2d_loader


__all__ = ['deimos_spectrum1D_reader', 'deimos_spectrum2D_reader']


@mosviz_spectrum1d_loader('DEIMOS 1D Spectrum')
def deimos_spectrum1D_reader(file_name):
    """
    Data loader for Keck/DEIMOS 1D spectra.

    This loads the 'Bxspf-B' (extension 1)
    and 'Bxspf-R' (extension 2) and appends them
    together to proudce the combined Red/Blue Spectrum
    along with their Wavelength and Inverse Variance
    arrays.
    """
    print("In deimos spec1d reader############################### ", file_name)
    hdulist = fits.open(file_name)
    data = Data(label='1D Spectrum')
    data.header = hdulist[1].header

    full_wl = np.append(hdulist[1].data['LAMBDA'][0], hdulist[2].data['LAMBDA'][0])
    full_spec = np.append(hdulist[1].data['SPEC'][0], hdulist[2].data['SPEC'][0])
    full_ivar = np.append(hdulist[1].data['IVAR'][0], hdulist[2].data['IVAR'][0])

    data.add_component(full_wl, 'Wavelength')
    data.add_component(full_spec, 'Flux')
    data.add_component(1 / np.sqrt(full_ivar), 'Uncertainty')

    return data


@mosviz_spectrum2d_loader('DEIMOS 2D Spectrum')
def deimos_spectrum2D_reader(file_name):
    """
    Data loader for Keck/DEIMOS 2D spectra.

    This loads only the Flux and Inverse variance.
    Wavelength information comes from the WCS.
    """

    hdulist = fits.open(file_name)
    data = Data(label='2D Spectrum')
    hdulist[1].header['CTYPE2'] = 'Spatial Y'
    wcs = WCS(hdulist[1].header)
    # original WCS has both axes named "LAMBDA", glue requires unique component names

    data.coords = coordinates_from_wcs(wcs)
    data.header = hdulist[1].header
    data.add_component(hdulist[1].data['FLUX'][0], 'Flux')
    data.add_component(1 / np.sqrt(hdulist[1].data['IVAR'][0]), 'Uncertainty')
    return data
