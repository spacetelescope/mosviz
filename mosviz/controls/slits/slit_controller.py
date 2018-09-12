import numpy as np
from .slit_selection_ui import SlitSelectionUI
from .rectangle_slit import RectanglePixelSlit, RectangleSkySlit


class SlitController:
    """
    Controller that stores MOSViz slits.
    """
    def __init__(self, mosviz_viewer=None):
        self.mosviz_viewer = mosviz_viewer

        self._slits = []

    @property
    def slits(self):
        return self._slits

    @property
    def has_slits(self):
        return len(self.slits) > 0

    @property
    def x_bounds(self):
        """
        Given all slits, return the lowermost
        and uppermost x pixel values.
        None if n/a.
        """
        if not self.has_slits:
            return
        x_max_list = []
        x_min_list = []
        for slit in self.slits:
            bounds = slit.x_bounds
            if bounds is None:
                continue
            xmin, xmax = bounds
            x_min_list.append(xmin)
            x_max_list.append(xmax)

        if len(x_max_list) > 0:
            return [min(x_min_list), max(x_max_list)]

    @property
    def y_bounds(self):
        """
        Given all slits, return the lowermost
        and uppermost y pixel values.
        None if n/a.
        """
        if not self.has_slits:
            return
        y_max_list = []
        y_min_list = []
        for slit in self.slits:
            bounds = slit.y_bounds
            if bounds is None:
                continue
            ymin, ymax = bounds
            y_min_list.append(ymin)
            y_max_list.append(ymax)

        if len(y_max_list) > 0:
            return [min(y_min_list), max(y_max_list)]

    def get_cutout_limit(self):
        """
        The limits of the cutout image viewer
        needs to match the y axis length of
        the slit to match the 2d spectrum viewer.
        This function calculates the x and y limits
        such that the viewer is displaying a y by y image.

        Returns
        -------
        plot_limits : list or None
            [x_min, x_max, y_min, y_max]
        """
        if not self.has_slits:
            return None

        # We want the image dimensions to be dy x dy
        y_bounds = self.y_bounds
        if y_bounds is None:
            return None
        y_min, y_max = y_bounds

        x_bounds = self.x_bounds
        if x_bounds is None:
            return None
        x_min, x_max = x_bounds

        # Calculate new x bounds (must be length of dy)
        dy = y_max - y_min
        x = (x_max + x_min) / 2.
        new_x_min, new_x_max = (x - dy / 2., x + dy / 2.)

        return [new_x_min, new_x_max, y_min, y_max]

    def add_slit(self, slit):
        self._slits.append(slit)

    def add_rectangle_sky_slit(self, wcs, ra, dec, width, length):
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
        self.add_slit(RectangleSkySlit(wcs, ra, dec, width, length))

    def add_rectangle_pixel_slit(self, x, y, width, length):
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
        self.add_slit(RectanglePixelSlit(x, y, width, length))

    def draw_slits(self, ax):
        for slit in self.slits:
            if slit.is_active:
                slit.remove()
            slit.draw(ax=ax)

    def clear_slits(self):
        """
        Reset slit controller and its variables.
        Remove the patch from the axes its drawn in.
        """
        for slit in self.slits:
            if slit.is_active:
                slit.remove()
            del slit
        self._slits = []

    def launch_slit_ui(self):
        """
        Launches UI for slit selection.
        """
        return SlitSelectionUI(self.mosviz_viewer, self.mosviz_viewer)
