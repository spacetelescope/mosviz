from ..third_party.qtpy.QtWidgets import *
from .graphs2d import ImageGraph, Spectrum2DGraph
from .graphs1d import Spectrum1DGraph


class UiMOSViewer(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(UiMOSViewer, self).__init__(*args, **kwargs)
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(2)

        self.graph1d = Spectrum1DGraph()
        self.graph2d = Spectrum2DGraph()
        self.graph_cutout = ImageGraph()
        self.meta_data = QTextEdit()

        self.grid_layout.addWidget(self.graph_cutout, 0, 0)
        self.grid_layout.addWidget(self.graph2d, 0, 2)
        self.grid_layout.addWidget(self.meta_data, 2, 0)
        self.grid_layout.addWidget(self.graph1d, 2, 2)


class MOSViewer(UiMOSViewer):
    def __init__(self, *args, **kwargs):
        super(MOSViewer, self).__init__(*args, **kwargs)

        pass