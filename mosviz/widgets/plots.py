import os

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QMainWindow

from matplotlib.patches import Rectangle

from glue.viewers.common.qt.toolbar import BasicToolbar
from glue.viewers.matplotlib.qt.widget import MplWidget
from glue.viewers.common.qt.tool import Tool
from glue.config import viewer_tool
from glue.utils import defer_draw


try:
    from glue.viewers.matplotlib.mpl_axes import init_mpl
except ImportError:  # glue < 0.14
    from glue.viewers.common.viz_client import init_mpl

from glue.viewers.image.qt.standalone_image_viewer import StandaloneImageViewer

__all__ = ['Line1DWidget', 'DrawableImageWidget', 'MOSImageWidget']

ICON_PATH = os.path.abspath(
    os.path.join(
        os.path.abspath(__file__),
        "..",
        "..",
        "data",
        "resources",
        "slit_icon.png"
    )
)
@viewer_tool
class SlitButton(Tool):
    """
    Image viewer tool to launch slit editor.
    """
    icon = ICON_PATH
    tool_id = 'mosviz:slit'
    action_text = ''
    tool_tip = 'Slit options'
    status_tip = ''
    shortcut = None

    def __init__(self, viewer):
        super(SlitButton, self).__init__(viewer)
        self.function = viewer.launch_slit_ui

    def activate(self):
        self.function()


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

    def _clear_artists(self):
        # Note: we can't use self._axes.cla() here since that removes events
        # which will cause the locked axes to not work.
        for artist in self._artists:
            try:
                artist.remove()
            except ValueError:  # some artists may already not be in plot
                pass

        for t in self.axes.texts:
            t.remove()

    def set_data(self, x, y, yerr=None):
        self._clear_artists()
        self.axes.set_axis_on()

        # Plot data
        if yerr is None:
            self._artists = self._axes.plot(x, y, color='k')
        else:
            self._artists = [self._axes.errorbar(x, y, yerr=yerr, color='k')]

        # Refresh canvas
        self._redraw()

    def no_data(self):
        self._clear_artists()
        self.axes.set_axis_off()

        xbounds = self.axes.get_xlim()
        if xbounds is None:
            return
        x = sum(xbounds) / 2.

        ybounds = self.axes.get_ylim()
        if ybounds is None:
            return
        y = sum(ybounds) / 2.

        fontdict = {"fontsize": 30,
                    "color": "black",
                    "ha": "center",
                    "va": "center"}

        self.axes.text(x, y, "No 1D Spectrum", fontdict=fontdict)
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


class Spectrum2DWidget(MOSImageWidget):

    def __init__(self, *args, **kwargs):
        super(MOSImageWidget, self).__init__(*args, **kwargs)

    def _clear_image(self):
        if self._im is not None:
            self._im.remove()
            self._im = None

    @defer_draw
    def set_image(self, image=None, wcs=None, **kwargs):
        #self.axes.set_axis_on()

        for c in self.axes.coords:
            c.set_ticks_visible(True)
            c.set_ticklabel_visible(True)

        for t in self.axes.texts:
            t.remove()
        super(MOSImageWidget, self).set_image(image, wcs, **kwargs)

    def no_data(self):
        self._clear_image()
        #self.axes.set_axis_off()

        for c in self.axes.coords:
            c.set_ticks_visible(False)
            c.set_ticklabel_visible(False)

        xbounds = self.axes.get_xlim()
        if xbounds is None:
            return
        x = sum(xbounds) / 2.

        ybounds = self.axes.get_ylim()
        if ybounds is None:
            return
        y = sum(ybounds) / 2.

        fontdict = {"fontsize": 30,
                    "color": "black",
                    "ha": "center",
                    "va": "center"}

        self.axes.text(x, y, "No 2D Spectrum", fontdict=fontdict)
        # Refresh canvas
        self._redraw()


class DrawableImageWidget(MOSImageWidget):
    tools = ['mpl:home', 'mpl:save', 'mpl:pan', 'mpl:zoom',
             'image:contrast', 'image:colormap', 'mosviz:slit']

    slit_controller = None

    def __init__(self, *args, slit_controller=None, **kwargs):
        super(DrawableImageWidget, self).__init__(*args, **kwargs)
        self._slit_patch = None
        self.slit_controller = slit_controller

    def draw_rectangle(self, x=None, y=None, width=None, height=None):
        if self._slit_patch is not None:
            self._slit_patch.remove()
        self._slit_patch = Rectangle((x - width / 2, y - height / 2),
                                     width=width, height=height,
                                     edgecolor='red', facecolor='none')
        self._axes.add_patch(self._slit_patch)

    def draw_slit(self):
        """
        Draw the slit patch stored in the slit controller.
        """
        if self.slit_controller.has_slits:
            self.slit_controller.draw_slits(self._axes)

    def set_limits(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """Manually set the limits of the axes."""
        self._axes.set_xlim(x_min, x_max)
        self._axes.set_ylim(y_min, y_max)

    def set_slit_limits(self):
        """Set y limits of plot according to slit length"""
        if self.slit_controller.has_slits:
            # We want the image dimensions to be dy x dy
            limits = self.slit_controller.get_cutout_limit()
            if limits is not None:
                self.set_limits(*limits)

    def reset_limits(self):
        """Auto set the limits of the axes."""
        self._axes.relim()

    def launch_slit_ui(self):
        self.slit_controller.launch_slit_ui()
