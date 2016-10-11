import os

from glue.qt.widgets.data_viewer import DataViewer
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.uic import loadUi

from ..widgets.toolbars import MOSViewerToolbar
from ..widgets.plots import Line1DWidget
from ..loaders.mos_loaders import *

from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget


class MOSVizViewer(DataViewer):
    LABEL = "MosViz Viewer"
    window_closed = Signal()
    _toolbar_cls = MOSViewerToolbar

    def __init__(self, session, parent=None):
        super(MOSVizViewer, self).__init__(session, parent=parent)
        self.central_widget = QWidget()

        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'widgets', 'ui', 'mos_widget.ui'))
        loadUi(path, self.central_widget)

        self.image2d = StandaloneImageWidget()
        self.spectrum2d = StandaloneImageWidget()
        self.spectrum1d = Line1DWidget()

        self.central_widget.left_vertical_splitter.insertWidget(0, self.image2d)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum2d)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum1d)

        # Set the splitter stretch factors
        self.central_widget.left_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.left_vertical_splitter.setStretchFactor(1, 2)

        self.central_widget.right_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.right_vertical_splitter.setStretchFactor(1, 2)

        self.central_widget.horizontal_splitter.setStretchFactor(0, 1)
        self.central_widget.horizontal_splitter.setStretchFactor(1, 2)

        # Set the central widget
        self.setCentralWidget(self.central_widget)

    def add_data(self, data):
        return True

    def options_widget(self):
        return None

    def register_to_hub(self, hub):
        super(MOSVizViewer, self).register_to_hub(hub)

        # hub.subscribe(self,
        #               DataUpdateMessage,
        #               handler=self._update_data)

    def _update_data(self, msg):
        pass

    def initialize_toolbar(self):

        # TODO: remove once Python 2 is no longer supported - see below for
        #       simpler code.

        from glue.config import viewer_tool

        self.toolbar = self._toolbar_cls(self)

        for tool_id in self.tools:
            mode_cls = viewer_tool.members[tool_id]
            mode = mode_cls(self)
            self.toolbar.add_tool(mode)

        self.addToolBar(self.toolbar)

