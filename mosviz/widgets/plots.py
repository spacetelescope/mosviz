import os

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QMainWindow

from matplotlib.patches import Rectangle

from glue.viewers.common.qt.toolbar import BasicToolbar
from glue.viewers.matplotlib.qt.widget import MplWidget
from glue.viewers.common.qt.tool import Tool
from glue.config import viewer_tool

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
        # self.slit_controller._pix_slit.plot(self.axes)  # Keep, may be used in the future
        if self.slit_controller.is_active:
            self._slit_patch = self.slit_controller.patch
            self._axes.add_patch(self._slit_patch)

    def set_limits(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """Manually set the limits of the axes."""
        self._axes.set_xlim(x_min, x_max)
        self._axes.set_ylim(y_min, y_max)

    def set_slit_limits(self):
        """Set y limits of plot according to slit length"""
        if self.slit_controller.is_active:
            # We want the image dimensions to be dy x dy
            dy = self.slit_controller.dy
            x = self.slit_controller.x
            x_min, x_max = (x - dy/2., x + dy/2.)
            y_min, y_max = self.slit_controller.y_bounds

            self.set_limits(x_min, x_max, y_min, y_max)

    def reset_limits(self):
        """Auto set the limits of the axes."""
        self._axes.relim()

    def launch_slit_ui(self):
        self.slit_controller.launch_slit_ui()
