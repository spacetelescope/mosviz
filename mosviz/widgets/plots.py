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
from matplotlib.patches import Rectangle
# rcParams.update({'figure.autolayout': True})

__all__ = ['Line1DWidget', 'DrawableImageWidget', 'MOSImageWidget']


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

        self._axes = self.figure.add_subplot(111)

    @property
    def axes(self):
        return self._axes

    def set_data(self, x, y, yerr=None):

        self._axes.cla()

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
        self._axes.set_adjustable('datalim')

    def set_status(self, status):
        pass


class DrawableImageWidget(MOSImageWidget):

    def __init__(self, *args, **kwargs):
        super(DrawableImageWidget, self).__init__(*args, **kwargs)
        self._slit_patch = None

    def draw_rectangle(self, x=None, y=None, width=None, height=None):
        if self._slit_patch is not None:
            self._slit_patch.remove()
        self._slit_patch = Rectangle((x - width / 2, y - height / 2),
                                     width=width, height=height,
                                     edgecolor='red', facecolor='none')
        self._axes.add_patch(self._slit_patch)
