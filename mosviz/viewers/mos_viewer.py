from ..third_party.qtpy.QtWidgets import *
from ..third_party.qtpy.QtCore import *
from ..third_party.qtpy.QtGui import *
from .graphs2d import ImageGraph, Spectrum2DGraph
from .graphs1d import Spectrum1DGraph
from ..ui.widgets.utils import ICON_PATH

import numpy as np


class UiMOSViewer(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(UiMOSViewer, self).__init__(*args, **kwargs)
        self.layout_vertical = QVBoxLayout()
        self.layout_horizontal = QHBoxLayout()

        self.tool_bar_mos_viewer = MOSToolBar()
        self.addToolBar(self.tool_bar_mos_viewer)

        self.graph1d = Spectrum1DGraph()
        self.graph2d = Spectrum2DGraph()
        self.graph_cutout = ImageGraph()
        self.meta_data = QTextEdit()
        self.meta_data.setReadOnly(True)

        splitter_horizontal = QSplitter()
        self.layout_vertical.addWidget(splitter_horizontal)

        splitter_vertical_right = QSplitter(Qt.Vertical)
        splitter_vertical_left = QSplitter(Qt.Vertical)

        splitter_horizontal.addWidget(splitter_vertical_left)
        splitter_horizontal.addWidget(splitter_vertical_right)

        splitter_vertical_left.addWidget(self.graph_cutout)
        splitter_vertical_left.addWidget(self.meta_data)
        splitter_vertical_right.addWidget(self.graph2d)
        splitter_vertical_right.addWidget(self.graph1d)

        splitter_horizontal.setStretchFactor(0, 1)
        splitter_horizontal.setStretchFactor(1, 3)

        splitter_vertical_left.setStretchFactor(0, 1)
        splitter_vertical_left.setStretchFactor(1, 3)

        splitter_vertical_right.setStretchFactor(0, 1)
        splitter_vertical_right.setStretchFactor(1, 3)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.layout_vertical)
        self.setCentralWidget(self.main_widget)


class MOSViewer(UiMOSViewer):
    def __init__(self, *args, **kwargs):
        super(MOSViewer, self).__init__(*args, **kwargs)
        self._data = None
        self._current_index = 0
        self._setup_connections()

    def _setup_connections(self):
        self.tool_bar_mos_viewer.combo_box_select.currentIndexChanged\
            .connect(self.current_data)

        self.tool_bar_mos_viewer.atn_prev.triggered.connect(
            lambda: self.current_data(self._current_index - 1))

        self.tool_bar_mos_viewer.atn_next.triggered.connect(
            lambda: self.current_data(self._current_index + 1))

    def _setup(self):
        self.tool_bar_mos_viewer.combo_box_select.clear()

        if self._data is None:
            self.tool_bar_mos_viewer.atn_prev.setEnabled(False)
            self.tool_bar_mos_viewer.atn_next.setEnabled(False)
            self.tool_bar_mos_viewer.combo_box_select.setEnabled(False)
        else:
            self.tool_bar_mos_viewer.atn_prev.setEnabled(True)
            self.tool_bar_mos_viewer.atn_next.setEnabled(True)
            self.tool_bar_mos_viewer.combo_box_select.setEnabled(True)

            self.tool_bar_mos_viewer.combo_box_select.insertItems(
                0, [x['id'] for x in self._data.collection])

    def set_data(self, data):
        self._data = data
        self._setup()
        self.current_data()

    def current_data(self, index=0):
        if 0 > index or index >= len(self._data.collection):
            return
        elif index == len(self._data.collection) - 1:
            self.tool_bar_mos_viewer.atn_next.setEnabled(False)
            self.tool_bar_mos_viewer.atn_prev.setEnabled(True)
        elif index == 0:
            self.tool_bar_mos_viewer.atn_prev.setEnabled(False)
            self.tool_bar_mos_viewer.atn_next.setEnabled(True)
        else:
            self.tool_bar_mos_viewer.atn_prev.setEnabled(True)
            self.tool_bar_mos_viewer.atn_next.setEnabled(True)

        self._current_index = index
        self.tool_bar_mos_viewer.combo_box_select.setCurrentIndex(self._current_index)

        data = self._data.collection[self._current_index]

        self.graph1d.plot.setData(data['spec1d'].data)
        self.graph2d.set_data(data['spec2d'].data)
        self.graph_cutout.set_data(data['image'].data)

        self.meta_data.setText("""id: blah
        other: blah
        """)


class MOSToolBar(QToolBar):
    def __init__(self, *args):
        super(MOSToolBar, self).__init__(*args)
        self.atn_next = QAction(QIcon(os.path.join(ICON_PATH,
                                                   "Next-48.png")),
                                "Next", self)
        self.atn_prev = QAction(QIcon(os.path.join(ICON_PATH,
                                                   "Previous-48.png")),
                                "Previous", self)

        self.combo_box_select = QComboBox()

        self.addAction(self.atn_prev)
        self.addWidget(self.combo_box_select)
        self.addAction(self.atn_next)