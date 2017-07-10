from __future__ import print_function, division, absolute_import

from qtpy import PYQT5
from qtpy.QtWidgets import QMainWindow
from qtpy.QtCore import Signal

import matplotlib.pyplot as plt
if PYQT5:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle

try:
    from glue.viewers.image.qt.standalone_image_viewer import StandaloneImageViewer
except ImportError:
    from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget as StandaloneImageViewer

from glue.viewers.common.viz_client import init_mpl
try:
    from glue.viewers.common.qt.mpl_toolbar import MatplotlibViewerToolbar
except ImportError:
    from glue.viewers.matplotlib.qt.toolbar import MatplotlibViewerToolbar


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

        _, self._axes = init_mpl(figure=self.figure)
        self._artists = []

    @property
    def axes(self):
        return self._axes

    def set_data(self, x, y, yerr=None):

        # Note: we can't use self._axes.cla() here since that removes events
        # which will cause the locked axes to not work.
        for artist in self._artists:
            try:
                artist.remove()
            except ValueError:  # some artists may already not be in plot
                pass

        # Plot data
        if yerr is None:
            self._artists = self._axes.plot(x, y, color='k')
        else:
            self._artists = [self._axes.errorbar(x, y, yerr=yerr, color='k')]

        # Refresh canvas
        self._redraw()

    def _redraw(self):
        self.central_widget.canvas.draw()

    def set_status(self, message):
        pass


class MOSImageWidget(StandaloneImageViewer):

    def __init__(self, *args, **kwargs):
        super(MOSImageWidget, self).__init__(*args, **kwargs)

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
