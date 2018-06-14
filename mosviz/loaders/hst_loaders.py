from astropy.io import fits
from glue.core import Data
from glue.core.coordinates import coordinates_from_header

from .utils import mosviz_cutout_loader


__all__ = ['acs_cutout_image_reader']


@mosviz_cutout_loader('ACS Cutout Image')
def acs_cutout_image_reader(file_name):
    """
    Data loader for the ACS cut-outs for the DEIMOS spectra.

    The cutouts contain only the image.
    """

    hdulist = fits.open(file_name)
    data = Data(label='ACS Cutout Image')
    data.coords = coordinates_from_header(hdulist[0].header)
    data.header = hdulist[0].header
    data.add_component(hdulist[0].data, 'Flux')

    return data
