from collections import defaultdict

from astropy.table import Table
from astropy import units as u

__all__ = ['Source', 'SourceCatalog',]


class Source:
    """
    An information container for a single source.
    Contributes a row in a mosviz table via the
    to_row method.

    Attributes
    ----------
    source_id : str
        ID of the source. Must be unique.

    spec1d : str
        1D spectrum file. "None" if n/a.

    spec2d : str
        2D spectrum file. "None" if n/a.

    cutout : str
        cutout image file. "None" if n/a.

    ra, dec : float
        Coordinates of source in degrees

    slit_width, slit_length : float
        Size of slit in arcsec

    spatial_pixel_scale : float
        Pixel scale in 2D spectrum in pixel/arcsec

    slit_pa : float
        Position angle of slit

    level2 : list
        A list of level 2 data files, added through
        the add_level2 function.
    """

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
            # TODO: Multiple level2 data
            return self._level2[0]

    def add_level2(self, file_name):
        """Append a level2 data product to list"""
        self._level2.append(file_name)

    def to_row(self, include_level2=False):
        """
        Return a list of attributes to be
        add to the astropy.table.Table.

        Returns
        -------
        row : list
            List of row data.
        """

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
    """
    A catalog (defaultdict) of Source objects that
    generates a MOSViz from the Sources. When a new
    source is added, the key of the source will become
    the Source's ID.

    Returns a `astropy.table.Table` via the to_table function.
    Writes table to an ecsv file via the to_file function.
    """
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
        """
        Convert catalog to `astropy.table.table`.
        """
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
        """
        Write catalog to ecsv file.

        Returns
        -------
        row : list
            List of row data.
        """
        t = self.to_table()
        if t is None:
            raise Exception("SourceCatalog is empty")
        t.write(save_file_name, format="ascii.ecsv", overwrite=True)

