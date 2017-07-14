import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
from glue.core import Data
from glue.core.coordinates import coordinates_from_header, coordinates_from_wcs

from .utils import mosviz_spectrum1d_loader, mosviz_spectrum2d_loader, mosviz_cutout_loader


__all__ = ['pre_nirspec_spectrum1d_reader', 'pre_nirspec_spectrum2d_reader',
           'pre_nircam_image_reader']


@mosviz_spectrum1d_loader("NIRSpec 1D Spectrum")
def nirspec_spectrum1d_reader(file_name):
    with fits.open(file_name) as hdulist:
        header = hdulist['PRIMARY'].header

    tab = Table.read(file_name)

    data = Data(label="1D Spectrum")
    data.header = header
    data.add_component(tab['WAVELENGTH'], "Wavelength")
    data.add_component(tab['FLUX'], "Flux")
    data.add_component(tab['ERROR'], "Uncertainty")

    return data


@mosviz_spectrum2d_loader('NIRSpec 2D Spectrum')
def nirspec_spectrum2d_reader(file_name):
    """
    Data loader for simulated NIRSpec 2D spectrum.

    This function extracts the DATA, QUALITY, and VAR
    extensions and returns them as a glue Data object.

    It then uses the header keywords of the DATA extension
    to detemine the wavelengths.
    """

    hdulist = fits.open(file_name)

    data = Data(label="2D Spectrum")
    data.header = hdulist['PRIMARY'].header
    data.coords = coordinates_from_header(hdulist[1].header)
    data.add_component(hdulist['SCI'].data, 'Flux')
    data.add_component(np.sqrt(hdulist['CON'].data), 'Uncertainty')

    hdulist.close()

    return data


@mosviz_spectrum1d_loader('Pre NIRSpec 1D Spectrum')
def pre_nirspec_spectrum1d_reader(file_name):
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
                             hdulist['DATA'].header['CRVAL1'] * hdulist['DATA'].header['CDELT1'],
                             hdulist['DATA'].header['NAXIS1'])[::-1]

    data = Data(label='1D Spectrum')
    data.header = hdulist['DATA'].header
    data.add_component(wavelength, 'Wavelength')
    data.add_component(hdulist['DATA'].data, 'Flux')
    data.add_component(np.sqrt(hdulist['VAR'].data), 'Uncertainty')

    hdulist.close()

    return data


@mosviz_spectrum2d_loader('Pre NIRSpec 2D Spectrum')
def pre_nirspec_spectrum2d_reader(file_name):
    """
    Data loader for simulated NIRSpec 2D spectrum.

    This function extracts the DATA, QUALITY, and VAR
    extensions and returns them as a glue Data object.

    It then uses the header keywords of the DATA extension
    to detemine the wavelengths.
    """

    hdulist = fits.open(file_name)

    data = Data(label='2D Spectrum')
    data.header = hdulist['DATA'].header
    data.coords = coordinates_from_header(hdulist[1].header)
    data.add_component(hdulist['DATA'].data, 'Flux')
    data.add_component(np.sqrt(hdulist['VAR'].data), 'Uncertainty')

    hdulist.close()

    return data


@mosviz_cutout_loader('NIRCam Image')
def pre_nircam_image_reader(file_name):
    """
    Data loader for simulated NIRCam image. This is for the
    full image, where cut-outs will be created on the fly.

    From the header:
    If ISWFS is T, structure is:

            -  Plane 1: Signal [frame3 - frame1] in ADU
            -  Plane 2: Signal uncertainty [sqrt(2*RN/g + \|frame3\|)]

    If ISWFS is F, structure is:

            -  Plane 1: Signal from linear fit to ramp [ADU/sec]
            -  Plane 2: Signal uncertainty [ADU/sec]

    Note that in the later case, the uncertainty is simply the formal
    uncertainty in the fit parameter (eg. uncorrelated, WRONG!). Noise
    model to be implemented at a later date.
    In the case of WFS, error is computed as SQRT(2*sigma_read + \|frame3\|)
    which should be a bit more correct - ~Fowler sampling.

    The FITS file has a single extension with a data cube.
    The data is the first slice of the cube and the uncertainty
    is the second slice.

    """

    hdulist = fits.open(file_name)
    data = Data(label='NIRCam Image')
    data.header = hdulist[0].header
    wcs = WCS(hdulist[0].header)

    # drop the last axis since the cube will be split
    data.coords = coordinates_from_wcs(wcs)
    data.add_component(hdulist[0].data, 'Flux')
    data.add_component(hdulist[0].data / 100, 'Uncertainty')

    hdulist.close()

    return data