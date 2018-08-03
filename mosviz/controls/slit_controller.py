import numpy as np

from glue.core import HubListener

from regions import RectangleSkyRegion

from matplotlib.patches import Rectangle

from astropy.coordinates import Angle, SkyCoord
from astropy.wcs.utils import proj_plane_pixel_area
from astropy import units as u


class SlitController(HubListener):
    def __init__(self, mosviz_viewer=None):
        super(SlitController, self).__init__()
        self.mosviz_viewer = mosviz_viewer

        self._slit = None
        self._pix_slit = None
        self._patch = None

    @property
    def is_active(self):
        return self._pix_slit is not None

    @property
    def patch(self):
        return self._patch

    @property
    def x(self):
        return self._pix_slit.center.x

    @property
    def y(self):
        return self._pix_slit.center.y

    @property
    def width(self):
        return self._pix_slit.width

    @property
    def length(self):
        return self._pix_slit.height

    @property
    def dx(self):
        return self._pix_slit.width

    @property
    def dy(self):
        return self._pix_slit.height

    def draw_rectangle(self, x=None, y=None, width=None, height=None):
        # if self._patch is not None:
        #     self._patch.remove()

        self._slit = Rectangle((x - width / 2, y - height / 2),
                               width=width, height=height,
                               edgecolor='red', facecolor='none')

        self._patch = self._slit  # self._slit.as_patch()

        print("draw_rectangle", self._patch.get_xy())

    def draw_rectangle2(self, x=None, y=None, width=None, height=None):
        if self._patch is not None:
            self._patch.remove()

        RectangleSkyRegion(center=SkyCoord(42, 43, unit='deg'),
        width = Angle(3, 'deg'), height = Angle(4, 'deg'),
        angle = Angle(5, 'deg'))

    def construct(self, wcs, ra, dec, slit_length, slit_width):
        self.destruct()

        skycoord = SkyCoord(ra, dec,
                            unit=(u.Unit(u.deg),
                                  u.Unit(u.deg)),
                            frame='fk5')

        length = Angle(slit_length, u.arcsec)
        width = Angle(slit_width, u.arcsec)

        self._slit = RectangleSkyRegion(center=skycoord, width=width, height=length)
        self._pix_slit = self._slit.to_pixel(wcs)
        self._patch = self._pix_slit.as_patch(edgecolor='green', facecolor='none')
        xp, yp = skycoord.to_pixel(wcs)
        xy = (ra, dec)
        self._patch.set_xy(xy)


        print("construct", self._patch.get_xy())

        print("sky", xp, yp)
        print("ra dec", ra, dec)



    def destruct(self):
        self._slit = None
        self._pix_slit = None

        # if self._patch is not None:
        #     self._patch.remove()
        self._patch = None
