from __future__ import absolute_import, division, print_function

from glue.config import data_factory
from glue.core import Data
from glue.core.coordinates import coordinates_from_header, coordinates_from_wcs
from astropy.io import fits
from astropy.wcs import WCS
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

@data_factory('NIRCam Image')
def nircam_image_reader(file_name):
    """
    Data loader for simulated NIRCam image. This is for the
    full image, where cut-outs will be created on the fly.

    From the header:
    If ISWFS is T, structure is:
            Plane 1: Signal [frame3 - frame1] in ADU
            Plane 2: Signal uncertainty [sqrt(2*RN/g + |frame3|)]
    If ISWFS is F, structure is:
            Plane 1: Signal from linear fit to ramp [ADU/sec]
            Plane 2: Signal uncertainty [ADU/sec]
    Note that in the later case, the uncertainty is simply the formal
    uncertainty in the fit parameter (eg. uncorrelated, WRONG!). Noise
    model to be implemented at a later date.
    In the case of WFS, error is computed as
      SQRT(2*sigma_read + |frame3|)
    which should be a bit more correct - ~Fowler sampling.

    The FITS file has a single extension with a data cube.
    The data is the first slice of the cube and the uncertainty
    is the second slice.
    """

    hdulist = fits.open(file_name)
    data = Data(label='NIRCam Image')
    wcs = WCS(hdulist[0].header)

    # drop the last axis since the cube will be split
    data.coords = coordinates_from_wcs(wcs.sub(2))
    data.add_component(hdulist[0].data[0], 'Signal [ADU/s]')
    data.add_component(hdulist[0].data[1], 'Uncertainty [ADU/s]')

    return data
