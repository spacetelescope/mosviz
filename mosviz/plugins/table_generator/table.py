from collections import defaultdict

from astropy.table import Table
from astropy import units as u

__all__ = ['Source', 'SourceCatalog',
           'SPEC_1D_KEY', 'SPEC_2D_KEY',
           'LEVEL2_KEY', 'CUTOUT_KEY',
           ]


SPEC_1D_KEY = 'spec_1d'
SPEC_2D_KEY = 'spec_2d'
LEVEL2_KEY = 'level2'
CUTOUT_KEY = 'cutouts'


class Source:
    def __init__(self):
        self.source_id = None

        self.spec1d = "None"
        self.spec2d = "None"
        self.cutout = "None"

        self.ra = None
        self.dec = None
        self.slit_width = None
        self.slit_length = None
        self.spatial_pixel_scale = None
        self.slit_pa = None

        self._level2 = []

    def __str__(self):
        return "{}\n\t{}\n\t{}\n\t{}".format(self.source_id,
                                             self.spec1d,
                                             self.spec2d,
                                             self.level2)

    @property
    def has_level2(self):
        if self._level2:
            return True
        return False

    @property
    def level2(self):
        if not self._level2:
            return "None"
        else:
            # Can only support 1 level2 in v0.3
            return self._level2[0]

    def add_level2(self, file_name):
        self._level2.append(file_name)

    def to_row(self, include_level2=False):
        row = [
            self.source_id,
            self.ra,
            self.dec,
            self.level2,
            self.spec1d,
            self.spec2d,
            self.cutout,
            self.slit_width,
            self.slit_length,
            self.spatial_pixel_scale,
            self.slit_pa]

        if not include_level2:
            row.pop(3)

        return row


class SourceCatalog(defaultdict):
    def __init__(self):
        super(SourceCatalog, self).__init__(Source)

    def __missing__(self, key):
        res = super().__missing__(key)
        res.source_id = key
        return res

    def has_level2(self):
        for source_id in self.keys():
            source = self.__getitem__(source_id)
            if source.has_level2:
                return True
        return False

    def to_table(self):
        if len(self.keys()) == 0:
            return

        has_level2 = self.has_level2()

        catalog = []
        for source_id in self.keys():
            source = self.__getitem__(source_id)
            catalog.append(source.to_row(has_level2))

        col_names = ["id", "ra", "dec", "level2",
                     "spectrum1d", "spectrum2d", "cutout",
                     "slit_width", "slit_length",
                     "spatial_pixel_scale", "slit_pa"]

        if not has_level2:
            col_names.pop(3)

        t = Table(rows=catalog, names=col_names)
        t["ra"].unit = u.deg
        t["dec"].unit = u.deg
        t["slit_width"].unit = u.arcsec
        t["slit_length"].unit = u.arcsec
        t["spatial_pixel_scale"].unit = (u.arcsec / u.pix)
        t["slit_pa"].unit = u.deg

        return t

    def to_file(self, save_file_name):
        t = self.to_table()
        if t is None:
            raise Exception("SourceCatalog is empty")
        t.write(save_file_name, format="ascii.ecsv", overwrite=True)

