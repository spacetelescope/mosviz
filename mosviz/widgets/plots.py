from qtpy.QtWidgets import QMainWindow, QWidget
from qtpy.QtCore import Signal

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget
from glue.viewers.common.qt.toolbar import BasicToolbar
try:
    from glue.viewers.common.qt.mpl_toolbar import MatplotlibViewerToolbar
except ImportError:
    from glue.viewers.matplotlib.qt.toolbar import MatplotlibViewerToolbar

import numpy as np
from astropy.wcs import WCS, WCSSUB_SPECTRAL

from matplotlib import rcParams
# rcParams.update({'figure.autolayout': True})

__all__ = ['Line1DWidget', 'ShareableAxesImageWidget',
           'DrawableImageWidget', 'MOSImageWidget']


class Line1DWidget(QMainWindow):
    window_closed = Signal()

    def __init__(self, parent=None):
        super(Line1DWidget, self).__init__(parent)

        self.figure = plt.figure(facecolor='white')

        # Canvas Widget that displays the `figure` it takes the `figure`
        # instance as a parameter to __init__
        canvas = FigureCanvas(self.figure)

        # Double reference; Glue's toolbar abstraction requires that the
        # central widget of its parent have a reference to the canvas object
        self.central_widget = canvas
        self.central_widget.canvas = canvas

        # Navigation widget, it takes the Canvas widget and a parent
        self.toolbar = MatplotlibViewerToolbar(self)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.central_widget)

        self._axes = None

    @property
    def axes(self):
        return self._axes

    def set_data(self, x, y, yerr=None):
        # Create an axis
        self._axes = self.figure.add_subplot(111)

        # Discards the old graph
        self._axes.hold(False)

        # Plot data
        if yerr is None:
            self._axes.plot(x, y)
        else:
            self._axes.errorbar(x, y, yerr=yerr)

        # Refresh canvas
        self._redraw()

    def _redraw(self):
        self.central_widget.canvas.draw()

    def set_status(self, message):
        pass


class MOSImageWidget(StandaloneImageWidget):

    def __init__(self, *args, **kwargs):
        super(MOSImageWidget, self).__init__(*args, **kwargs)

    def set_image(self, image=None, wcs=None, header=None, **kwargs):
        super(MOSImageWidget, self).set_image(image, wcs, **kwargs)

        if header is not None:
            hwcs = WCS(header)

            # Try to reference the spectral axis
            hwcs_spec = hwcs.sub([WCSSUB_SPECTRAL])

            # Check to see if it actually is a real coordinate description
            if hwcs_spec.naxis == 0:
                # It's not real, so attempt to get the spectral axis by
                # specifying axis by integer
                hwcs_spec = hwcs.sub([hwcs.naxis])

            # Construct the dispersion array
            dispersion = hwcs_spec.all_pix2world(
                np.arange(image.shape[0]), 0)[0]

            self.axes.set_xticklabels(["{}".format(x) for x in dispersion])

    def set_status(self, status):
        pass

class ShareableAxesImageWidget(MOSImageWidget):
    def __init__(self, *args, **kwargs):
        super(ShareableAxesImageWidget, self).__init__(*args, **kwargs)

    def set_locked_axes(self, sharex=None, sharey=None):
        if sharex is not None and sharex is not False:
            self.axes._shared_x_axes.join(self.axes, sharex)
            if sharex._adjustable == 'box':
                sharex._adjustable = 'datalim'
                #warnings.warn(
                #    'shared axes: "adjustable" is being changed to "datalim"')
            self._adjustable = 'datalim'
        elif self._axes._sharex is not None and sharex is False:
            self.axes._shared_x_axes.remove(self._axes._sharex)

        if sharey is not None and sharey is not False:
            self.axes._shared_y_axes.join(self.axes, sharey)
            if sharey._adjustable == 'box':
                sharey._adjustable = 'datalim'
                #warnings.warn(
                #    'shared axes: "adjustable" is being changed to "datalim"')
            self._adjustable = 'datalim'
        elif self._axes._sharey is not None and sharey is False:
            self.axes._shared_y_axes.remove(self._axes._sharey)

        self._axes._sharex = sharex
        self._axes._sharey = sharey


class DrawableImageWidget(MOSImageWidget):

    def __init__(self, *args, **kwargs):
        super(DrawableImageWidget, self).__init__(*args, **kwargs)
        self._slit_patch = None

    def draw_shapes(self, x=0, y=0, width=100, length=100):
        self._slit_patch = plt.Rectangle((x-length, y-width), width, length, fc='r')
        # self.axes.add_patch(self._slit_patch)
