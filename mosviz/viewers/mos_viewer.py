from ..third_party.qtpy.QtWidgets import *
from ..third_party.qtpy.QtCore import *
from ..third_party.qtpy.QtGui import *
from .graphs2d import ImageGraph, Spectrum2DGraph
from .graphs1d import Spectrum1DGraph
from ..ui.widgets.utils import ICON_PATH
import six


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
        self.meta_data = QFormLayout()

        self.graph1d.setStyleSheet("""
            border:1px solid #999999;
            """)
        self.layout_graph1d_vertical = QVBoxLayout()
        self.layout_graph1d_vertical.setContentsMargins(2, 2, 2, 2)
        self.layout_graph1d_horizontal = QHBoxLayout()
        self.widget_graph1d_pos_label = QLabel()
        self.widget_graph1d_pos_label.setText("Pos: 0, 0 | Value: 0.0")
        self.layout_graph1d_vertical.addWidget(self.graph1d)
        self.layout_graph1d_horizontal.addWidget(self.widget_graph1d_pos_label)
        self.layout_graph1d_vertical.addLayout(self.layout_graph1d_horizontal)
        self.widget_graph1d = QWidget()
        self.widget_graph1d.setLayout(self.layout_graph1d_vertical)
        # self.widget_graph1d.setContentsMargins(1, 1, 1, 1)


        self.graph2d.setStyleSheet("""
            border:1px solid #999999;
            """)
        self.layout_graph2d_vertical = QVBoxLayout()
        self.layout_graph2d_vertical.setContentsMargins(2, 2, 2, 2)
        self.layout_graph2d_horizontal = QHBoxLayout()
        self.widget_graph2d_pos_label = QLabel()
        self.widget_graph2d_pos_label.setText("Pos: 0, 0 | Value: 0.0")
        self.layout_graph2d_vertical.addWidget(self.graph2d)
        self.layout_graph2d_horizontal.addWidget(self.widget_graph2d_pos_label)
        self.layout_graph2d_vertical.addLayout(self.layout_graph2d_horizontal)
        self.widget_graph2d = QWidget()
        self.widget_graph2d.setLayout(self.layout_graph2d_vertical)
        # self.widget_graph2d.setContentsMargins(1, 1, 1, 1)


        self.graph_cutout.setStyleSheet("""
            border:1px solid #999999;
            """)
        self.layout_graph_cutout_vertical = QVBoxLayout()
        self.layout_graph_cutout_vertical.setContentsMargins(2, 2, 2, 2)
        self.layout_graph_cutout_horizontal = QHBoxLayout()
        self.widget_graph_cutout_pos_label = QLabel()
        self.widget_graph_cutout_pos_label.setText("Pos: 0, 0 | Value: 0.0")
        self.layout_graph_cutout_vertical.addWidget(self.graph_cutout)
        self.layout_graph_cutout_horizontal.addWidget(
            self.widget_graph_cutout_pos_label)
        self.layout_graph_cutout_vertical.addLayout(self.layout_graph_cutout_horizontal)
        self.widget_graph_cutout = QWidget()
        self.widget_graph_cutout.setLayout(self.layout_graph_cutout_vertical)
        # self.widget_graph_cutout.setContentsMargins(1, 1, 1, 1)

        # self.layout_meta_data_vertical = QVBoxLayout()
        # self.layout_meta_data_vertical.setContentsMargins(2, 2, 2, 2)
        # self.layout_meta_data_vertical.addLayout(self.meta_data)
        self.widget_meta_data = QWidget()
        self.widget_meta_data.setLayout(self.meta_data)
        self.meta_data_list = ["id", "ra", "dec", "spectrum1d", "spectrum2d",
                               "cutout", "slit_width", "slit_length",
                               "pix_scale"]
        self.meta_data_dict = {}
        # self.widget_meta_data.setContentsMargins(1, 1, 1, 1)

        # self.graph1d.setContentsMargins(11, 11, 11, 11)
        # self.graph2d.setContentsMargins(11, 11, 11, 11)
        # self.graph_cutout.setContentsMargins(11, 11, 11, 11)
        # self.meta_data.setContentsMargins(11, 11, 11, 11)

        splitter_horizontal = QSplitter()
        splitter_horizontal.setStyleSheet("""
            QSplitter::handle {
                background-color: #cccccc;
            }
            """)
        self.layout_vertical.addWidget(splitter_horizontal)

        splitter_vertical_right = QSplitter(Qt.Vertical)
        splitter_vertical_left = QSplitter(Qt.Vertical)

        splitter_horizontal.addWidget(splitter_vertical_left)
        splitter_horizontal.addWidget(splitter_vertical_right)

        splitter_vertical_left.addWidget(self.widget_graph_cutout)
        splitter_vertical_left.addWidget(self.widget_meta_data)
        splitter_vertical_right.addWidget(self.widget_graph2d)
        splitter_vertical_right.addWidget(self.widget_graph1d)

        splitter_horizontal.setStretchFactor(0, 1)
        splitter_horizontal.setStretchFactor(1, 3)

        splitter_vertical_left.setStretchFactor(0, 1)
        splitter_vertical_left.setStretchFactor(1, 3)

        splitter_vertical_right.setStretchFactor(0, 1)
        splitter_vertical_right.setStretchFactor(1, 3)

        self.main_widget = QWidget()
        self.main_widget.setContentsMargins(0, 0, 0, 0)
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

        # Connect toggling of color maps
        self.tool_bar_mos_viewer.atn_toggle_color_map.triggered.connect(
            lambda: self.toggle_color_maps(
                self.tool_bar_mos_viewer.atn_toggle_color_map.isChecked()))

        # Connect toggling x axes
        self.tool_bar_mos_viewer.atn_toggle_lock_x.triggered.connect(
            lambda: self.toggle_lock_x(
                self.tool_bar_mos_viewer.atn_toggle_lock_x.isChecked()))

        # Connect toggling y axes
        self.tool_bar_mos_viewer.atn_toggle_lock_y.triggered.connect(
            lambda: self.toggle_lock_y(
                self.tool_bar_mos_viewer.atn_toggle_lock_y.isChecked()))

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

        data = self._data[self._current_index]

        self.graph1d.set_data(data['spec1d'])
        self.graph2d.set_data(data['spec2d'])
        self.graph_cutout.set_data(data['image'])

        # Resize plots to fit data
        self.graph1d.plot.getViewBox().autoRange()
        self.graph2d.image_item.getViewBox().autoRange()
        self.graph_cutout.image_item.getViewBox().autoRange()

        for k, v in data.items():
            if k in ['spec1d', 'spec2d', 'image']:
                continue

            if k not in self.meta_data_dict:
                new_line_edit = QLineEdit()
                new_line_edit.setReadOnly(True)
                new_line_edit.setText("{}".format(v))
                self.meta_data_dict[k] = new_line_edit
                self.meta_data.addRow(k, new_line_edit)

            self.meta_data_dict[k].setText("{}".format(v))

    def toggle_color_maps(self, show):
        self.graph2d.toggle_color_map(show)
        self.graph_cutout.toggle_color_map(show)

    def toggle_lock_x(self, lock):
        self.graph2d.vb.setXLink(self.graph1d.vb if lock else None)

    def toggle_lock_y(self, lock):
        self.graph2d.vb.setYLink(self.graph_cutout.vb if lock else None)


class MOSToolBar(QToolBar):
    def __init__(self, *args):
        super(MOSToolBar, self).__init__(*args)
        self.atn_next = QAction(QIcon(os.path.join(ICON_PATH, "Next-48.png")),
                                "Next", self)
        self.atn_prev = QAction(
            QIcon(os.path.join(ICON_PATH, "Previous-48.png")),
            "Previous", self)
        self.combo_box_select = QComboBox()

        toggle_menu = QMenu()
        self.atn_toggle_lock_x = toggle_menu.addAction("Link X Axes")
        self.atn_toggle_lock_x.setCheckable(True)
        self.atn_toggle_lock_y = toggle_menu.addAction("Link Y Axes")
        self.atn_toggle_lock_y.setCheckable(True)
        self.atn_toggle_color_map = toggle_menu.addAction("Show color bars")
        self.atn_toggle_color_map.setCheckable(True)

        toggle_tool_button = QToolButton()
        toggle_tool_button.setText("Options")
        toggle_tool_button.setIcon(
            QIcon(os.path.join(ICON_PATH, "Settings 3-50.png")))
        toggle_tool_button.setMenu(toggle_menu)
        toggle_tool_button.setPopupMode(QToolButton.InstantPopup)

        self.addAction(self.atn_prev)
        self.addWidget(self.combo_box_select)
        self.addAction(self.atn_next)
        self.addSeparator()
        self.addWidget(toggle_tool_button)