from mosviz.interfaces.decorators import data_loader
from mosviz.core.data import Image

import os

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty


def fits_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            args[0].lower().split('.')[-1] in ['fits', 'fit'])


@data_loader(label="mos-image", identifier=fits_identify, data_class=Image)
def generic_image_loader(file_name, **kwargs):
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, memmap=True, **kwargs)

    header = hdulist[0].header
    meta = {'header': header}
    wcs = WCS(hdulist[0].header)
    unit = Unit('Jy')
    data = hdulist[0].data

    hdulist.close()

    return Image(data=data, name=name, wcs=wcs, unit=unit, meta=meta)