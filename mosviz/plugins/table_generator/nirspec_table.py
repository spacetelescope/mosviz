import os
from glob import glob, iglob
from collections import defaultdict

from astropy.io import fits
from astropy.table import Table
from astropy import units as u

from .table import *

SPEC_1D_KEY = 'spec_1d'
SPEC_2D_KEY = 'spec_2d'
LEVEL2_KEY = 'level2'
CUTOUT_KEY = 'cutouts'


def nirspec_table_generator(path, cutout_path=None, output_path=None):

    file_list = {
        SPEC_1D_KEY: [],
        SPEC_2D_KEY: [],
        LEVEL2_KEY:  [],
        CUTOUT_KEY:  [],
    }

    search_pattern = {
        SPEC_1D_KEY: "*x1d*fits*",
        SPEC_2D_KEY: "*s2d*fits*",
        LEVEL2_KEY:  "*cal*fits*",
        CUTOUT_KEY:  "*.fits*"
    }

    for file_type in file_list:
        search_path = os.path.join(path, "**", search_pattern[file_type])
        file_list[file_type] = [fn for fn in glob(search_path, recursive=True)]

    catalog = SourceCatalog()

    for x1d in file_list[SPEC_1D_KEY]:
        with fits.open(x1d) as hdul:
            for ext, h in enumerate(hdul):
                if h.name.upper() == 'EXTRACT1D':
                    header = h.header

                    source = catalog[str(header['SOURCEID'])]
                    source.spec1d = "{}[{}]".format(x1d, ext)
                    source.ra = header['SLIT_RA']
                    source.dec = header['SLIT_DEC']
                    source.slit_width = 0.2
                    source.slit_length = 3.3

    for s2d in file_list[SPEC_2D_KEY]:
        with fits.open(s2d) as hdul:
            for ext, h in enumerate(hdul):
                if h.name.upper() == 'SCI':
                    header = h.header

                    source = catalog[str(header['SOURCEID'])]
                    source.spec2d = "{}[{}]".format(s2d, ext)
                    source.spatial_pixel_scale = header['CDELT2']
                    source.slit_pa = header['PA_APER']

    if file_list[LEVEL2_KEY]:
        for lv2 in file_list[LEVEL2_KEY]:
            with fits.open(lv2) as hdul:
                for ext, h in enumerate(hdul):
                    if h.name == 'SCI':
                        header = h.header
                        if str(header['SOURCEID']) in catalog:
                            source = catalog[str(header['SOURCEID'])]
                            source.add_level2("{}[{}]".format(lv2, ext))

    if cutout_path is not None:
        for source_id in catalog:
            cutout = "{}.fits".format(source_id)
            cutout = os.path.join(cutout_path, cutout)
            if os.path.isfile(cutout):
                catalog[source_id].cutout = cutout

    if output_path is not None:
        catalog.to_file(output_path)

    return catalog
