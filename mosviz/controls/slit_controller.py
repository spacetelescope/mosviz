import numpy as np

from glue.core import HubListener

from regions import RectangleSkyRegion, RectanglePixelRegion, PixCoord

from matplotlib.patches import Rectangle

from astropy.coordinates import Angle, SkyCoord
from astropy.wcs.utils import proj_plane_pixel_area
from astropy import units as u

from ..controls.slit_selection_ui import SlitSelectionUI


class SlitController(HubListener):
    """
    Controller that constructs and stores
    a rectangular slit.
    """

    def __init__(self, mosviz_viewer=None):
        super(SlitController, self).__init__()
        self.mosviz_viewer = mosviz_viewer

        self._slit = None  # `region.RectangleSkyRegion` object
        self._pix_slit = None  # `region.RectanglePixelRegion` object
        self._patch = None  # `matplotlib.patches.Rectangle` patch

    @property
    def is_active(self):
        return self._patch is not None

    @property
    def patch(self):
        return self._patch

    @property
    def x(self):
        """Center x position of slit"""
        if self.is_active:
            return self.patch.get_x() + self.patch.get_width() / 2.

    @property
    def y(self):
        """Center y position of slit"""
        if self.is_active:
            return self.patch.get_y() + self.patch.get_height() / 2.

    @property
    def width(self):
        if self.is_active:
            return self.patch.get_width()

    @property
    def length(self):
        if self.is_active:
            return self.patch.get_height()

    @property
    def dx(self):
        """Width of slit"""
        return self.width

    @property
    def dy(self):
        """Length of slit"""
        return self.length

    @property
    def x_bounds(self):
        """x axis max and min pixel values"""
        xp = self.x
        dx = self.dx
        x_min = xp - dx / 2.
        x_max = xp + dx / 2.
        return [x_min, x_max]

    @property
    def y_bounds(self):
        """y axis max and min pixel values"""
        yp = self.y
        dy = self.dy
        y_min = yp - dy / 2.
        y_max = yp + dy / 2.
        return [y_min, y_max]

    def construct_simple_rectangle(self, x=None, y=None, width=None, length=None):
        """
        Simple matplotlib rectangle patch.

        Parameters
        ----------
        x, y : float
            Center (x, y) of slit in pix.
        width, length : float
            width and length of slit in pix.
        Returns
        -------
        patch : `matplotlib.patches.Rectangle`
        """
        self.destruct()

        self._slit = None
        self._pix_slit = None
        self._patch = Rectangle((x - width / 2, y - length / 2),
                                width=width, height=length,
                                edgecolor='red', facecolor='none')
        return self._patch

    def construct_pix_region(self, x, y, width, length):
        """
        Slit constructed using WCS and coords information.
        Utilizes `regions` package.

        Parameters
        ----------
        x, y : float
            Center (x, y) of slit in pix.
        width, length : float
            width and length of slit in pix.
        Returns
        -------
        patch : `matplotlib.patches.Rectangle`
        """
        self.destruct()

        pixcoord = PixCoord(x, y)

        self._slit = None
        self._pix_slit = RectanglePixelRegion(center=pixcoord, width=width, height=length)
        self._patch = self._pix_slit.as_artist(edgecolor='red', facecolor='none')

        return self._patch

    def construct_sky_region(self, wcs, ra, dec, width, length):
        """
        Slit constructed using WCS and coords information.
        Utilizes `regions` package.

        Parameters
        ----------
        wcs : `astropy.wcs.WCS`
        ra, dec : float
            Center (ra, dec) of slit in deg.
        width, length : float
            Angular width and length of slit in arcsec.

        Returns
        -------
        patch : `matplotlib.patches.Rectangle`
        """
        self.destruct()

        skycoord = SkyCoord(ra, dec,
                            unit=(u.Unit(u.deg),
                                  u.Unit(u.deg)),
                            frame='fk5')

        length = Angle(length, u.arcsec)
        width = Angle(width, u.arcsec)

        self._slit = RectangleSkyRegion(center=skycoord, width=width, height=length)
        self._pix_slit = self._slit.to_pixel(wcs)
        self._patch = self._pix_slit.as_artist(edgecolor='red', facecolor='none')

        return self._patch

    def move(self, x, y):
        """
        Move the bottom right corner of the patch.

        Parameters
        ----------
        x, y : float
            Center (x, y) of slit in pix.

        Returns
        -------
        bool : true if success.
        """
        if self.is_active:
            x_corner, y_corner = (x - self.width / 2, y - self.length / 2)
            self._patch.set_xy((x_corner, y_corner))
            return True
        return False

    def destruct(self):
        """
        Reset slit controller and its variables.
        Remove the patch from the axes its drawn in.
        """
        self._slit = None
        self._pix_slit = None
        if self._patch is not None:
            if self._patch._remove_method is not None:
                self._patch.remove()
        self._patch = None

    def launch_slit_ui(self):
        """
        Launches UI for slit selection.
        """
        return SlitSelectionUI(self.mosviz_viewer, self.mosviz_viewer)
