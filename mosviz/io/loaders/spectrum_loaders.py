from mosviz.interfaces.decorators import data_loader
from mosviz.core.data import GenericSpectrum1D
from mosviz.core.data import Spectrum2D

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


@data_loader(label="spectrum1d", identifier=fits_identify,
             data_class=GenericSpectrum1D)
def generic_spectrum1d_loader(file_name, **kwargs):
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, memmap=True, **kwargs)

    header = hdulist[0].header
    meta = {'header': header}
    wcs = WCS(hdulist[0].header)
    unit = Unit('Jy')
    uncertainty = StdDevUncertainty(hdulist[3].data)
    data = hdulist[1].data
    mask = hdulist[2].data

    hdulist.close()

    return GenericSpectrum1D(data=data, name=name, wcs=wcs,
                             uncertainty=uncertainty, unit=unit, meta=meta,
                             mask=mask)


@data_loader(label="spectrum2d", identifier=lambda x: x,
             data_class=Spectrum2D)
def generic_spectrum1d_loader(file_name, **kwargs):
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, memmap=True, **kwargs)

    header = hdulist[0].header
    meta = {'header': header}
    wcs = WCS(hdulist[0].header)
    unit = Unit('Jy')
    uncertainty = StdDevUncertainty(hdulist[3].data)
    data = hdulist[1].data
    mask = hdulist[2].data

    hdulist.close()

    return Spectrum2D(data=data, name=name, wcs=wcs, uncertainty=uncertainty,
                      unit=unit, meta=meta, mask=mask)

