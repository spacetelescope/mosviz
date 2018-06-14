from __future__ import print_function, division, absolute_import

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QMainWindow

from matplotlib.patches import Rectangle

from glue.viewers.common.qt.toolbar import BasicToolbar
from glue.viewers.matplotlib.qt.widget import MplWidget

try:
    from glue.viewers.matplotlib.mpl_axes import init_mpl
except ImportError:  # glue < 0.14
    from glue.viewers.common.viz_client import init_mpl

from glue.viewers.image.qt.standalone_image_viewer import StandaloneImageViewer

__all__ = ['Line1DWidget', 'DrawableImageWidget', 'MOSImageWidget']


class Line1DWidget(QMainWindow):

    window_closed = Signal()

    _toolbar_cls = BasicToolbar
    tools = ['mpl:home', 'mpl:save', 'mpl:pan', 'mpl:zoom']

    def __init__(self, parent=None):

        super(Line1DWidget, self).__init__(parent)

        self.central_widget = MplWidget()
        self.setCentralWidget(self.central_widget)
        _, self._axes = init_mpl(figure=self.central_widget.canvas.fig)

        self.initialize_toolbar()

        self._artists = []

    def initialize_toolbar(self):

        from glue.config import viewer_tool

        self.toolbar = self._toolbar_cls(self)

        for tool_id in self.tools:
            mode_cls = viewer_tool.members[tool_id]
            mode = mode_cls(self)
            self.toolbar.add_tool(mode)

        self.addToolBar(self.toolbar)

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

    tools = ['mpl:home', 'mpl:save', 'mpl:pan', 'mpl:zoom',
             'image:contrast', 'image:colormap']

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
