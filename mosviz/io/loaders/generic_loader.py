from mosviz.interfaces.decorators import data_loader
from mosviz.core.data import MOSData

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


@data_loader(label="Simple Generic", identifier=fits_identify, data_class=MOSData)
def simple_generic_loader(file_name, **kwargs):
    print("LOADING {}".format(file_name))
    mos_data = MOSData()

    name = os.path.basename(file_name.name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, **kwargs)

    header = hdulist[0].header

    tab = Table.read(file_name)

    meta = {'header': header}
    wcs = WCS(hdulist[0].header)
    unit = Unit('Jy')
    uncertainty = StdDevUncertainty(tab["err"])
    data = tab["flux"]

    hdulist.close()

    return mos_data

