from mosviz.interfaces.decorators import data_loader
from mosviz.core.data import MOSData

import os

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty


def catalog_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            args[0].lower().split('.')[-1] in ['txt', 'dat'])


@data_loader(label="MOS Catalog", identifier=catalog_identify,
             data_class=MOSData)
def generic_mos_loader(file_name, **kwargs):
    tab = Table.read(file_name, format='ascii.ecsv')
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    mos_data = MOSData(name=name)

    for i in range(len(tab)):
        file_path = '/'.join(file_name.split('/')[:-1])

        mos_data.load(id=tab[i]['id'],
                      spec1d_path=os.path.join(file_path,
                                               tab[i]['spectrum1d']),
                      spec2d_path=os.path.join(file_path,
                                               tab[i]['spectrum2d']),
                      image_path=os.path.join(file_path, tab[i]['cutout']),
                      ra=tab[i]['ra'], dec=tab[i]['dec'],
                      slit_width=tab[i]['slit_width'],
                      pix_scale=tab[i]['pix_scale'])

    return mos_data


def mos_glue_identify(*args, **kwargs):
    """
    This loader expects a dictionary composed of values from a Glue
    component object.
    """
    return isinstance(args[0], dict)


@data_loader(label="mos-glue", identifier=mos_glue_identify,
             data_class=MOSData)
def mos_glue_loader(catalog_list, **kwargs):
    print("Loading from: ", catalog_list)

    for mos_dict in catalog_list:
        mos_data = MOSData.load(spec1d_path=mos_dict['spectrum1d'],
                                spec2d_path=mos_dict['spectrum2d'],
                                image_path=mos_dict['cutout'])

    return mos_data
