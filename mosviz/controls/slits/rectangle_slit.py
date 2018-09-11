import numpy as np

from regions import RectangleSkyRegion, RectanglePixelRegion, PixCoord
from astropy.coordinates import Angle, SkyCoord
from astropy import units as u

from .slit_base import _MOSVizSlit


class _RectangleSlitBase(_MOSVizSlit):
    """Implements abstract functions for rectangular slits"""
    _patch = None  # `matplotlib.patches.Rectangle` patch
    _is_active = False

    @property
    def is_active(self):
        return self._is_active

    @property
    def has_patch(self):
        return self._patch is not None

    @property
    def patch(self):
        return self._patch

    @property
    def width(self):
        if self.has_patch:
            return self.patch.get_width()

    @property
    def length(self):
        if self.has_patch:
            return self.patch.get_height()

    @property
    def x(self):
        """Center x position of slit"""
        if self.has_patch:
            return self.patch.get_x() + self.patch.get_width() / 2.

    @property
    def y(self):
        """Center y position of slit"""
        if self.has_patch:
            return self.patch.get_y() + self.patch.get_height() / 2.

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
        if None in [xp, dx]:
            return
        x_min = xp - dx / 2.
        x_max = xp + dx / 2.
        return (x_min, x_max)

    @property
    def y_bounds(self):
        """y axis max and min pixel values"""
        yp = self.y
        dy = self.dy
        if None in [yp, dy]:
            return
        y_min = yp - dy / 2.
        y_max = yp + dy / 2.
        return (y_min, y_max)

    def draw(self, ax=None):
        self._is_active = True
        ax.add_patch(self._patch)

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
        if self.has_patch:
            x_corner, y_corner = (x - self.width / 2, y - self.length / 2)
            self._patch.set_xy((x_corner, y_corner))
        else:
            raise Exception("This slit's matplotlib.patches.Rectangle not found")

    def remove(self):
        self._is_active = False
        if self.has_patch:
            if self._patch._remove_method is not None:
                self._patch.remove()


class RectangleSkySlit(_RectangleSlitBase):
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
    """

    def __init__(self, wcs, ra, dec, width, length, *args, **kwargs):
        self.wcs = wcs

        skycoord = SkyCoord(ra, dec,
                            unit=(u.Unit(u.deg),
                                  u.Unit(u.deg)),
                            frame='fk5')

        length = Angle(length, u.arcsec)
        width = Angle(width, u.arcsec)

        self._sky_region = RectangleSkyRegion(center=skycoord, width=width, height=length)

        # N.B: The following step will not be needed when
        # regions.RectangleSkyRegion.as_artist is implemented
        self._pix_region = self._sky_region.to_pixel(wcs)
        self._patch = self._pix_region.as_artist(edgecolor='red', facecolor='none')
        self._is_active = False


class RectanglePixelSlit(_RectangleSlitBase):
    """
    Slit constructed using WCS and coords information.
    Utilizes `regions` package.

    Parameters
    ----------
    x, y : float
        Center (x, y) of slit in pix.
    width, length : float
        width and length of slit in pix.
   """
    def __init__(self, x=None, y=None, width=None, length=None, *args, **kwargs):
        pixcoord = PixCoord(x, y)
        self._pix_region = RectanglePixelRegion(center=pixcoord, width=width, height=length)
        self._patch = self._pix_region.as_artist(edgecolor='red', facecolor='none')
        self._is_active = False
        # N.B: self._pix_region.plot(self.axes) may be used to draw in the future
