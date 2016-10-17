import os

from glue.qt.widgets.data_viewer import DataViewer
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.uic import loadUi

from ..widgets.toolbars import MOSViewerToolbar
from ..widgets.plots import Line1DWidget
from ..loaders.mos_loaders import *
from ..widgets.viewer_options import OptionsWidget

from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget
from glue.core import message as msg
from glue.core import Subset
from glue.core.exceptions import IncompatibleAttribute
from astropy.table import Table


class MOSVizViewer(DataViewer):
    LABEL = "MosViz Viewer"
    window_closed = Signal()
    _toolbar_cls = MOSViewerToolbar

    def __init__(self, session, parent=None):
        super(MOSVizViewer, self).__init__(session, parent=parent)
        self.load_ui()

        # Define some data containers
        self.catalog = None

    def load_ui(self):
        """
        Setup the MOSView viewer interface.
        """
        self.central_widget = QWidget()

        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'widgets', 'ui', 'mos_widget.ui'))
        loadUi(path, self.central_widget)

        self.image_widget = StandaloneImageWidget()
        self.spectrum2d_widget = StandaloneImageWidget()
        self.spectrum1d_widget = Line1DWidget()

        self.central_widget.left_vertical_splitter.insertWidget(0, self.image_widget)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum2d_widget)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum1d_widget)

        # Set the splitter stretch factors
        self.central_widget.left_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.left_vertical_splitter.setStretchFactor(1, 2)

        self.central_widget.right_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.right_vertical_splitter.setStretchFactor(1, 2)

        self.central_widget.horizontal_splitter.setStretchFactor(0, 1)
        self.central_widget.horizontal_splitter.setStretchFactor(1, 2)

        # Set the central widget
        self.setCentralWidget(self.central_widget)

        # Define the options widget
        self._options_widget = OptionsWidget()

    def options_widget(self):
        return self._options_widget

    def initialize_toolbar(self):
        """
        Initialize the custom toolbar for the MOSViz viewer.
        """
        from glue.config import viewer_tool

        self.toolbar = self._toolbar_cls(self)

        for tool_id in self.tools:
            mode_cls = viewer_tool.members[tool_id]
            mode = mode_cls(self)
            self.toolbar.add_tool(mode)

        self.addToolBar(self.toolbar)

        # Connect the selection event for the combo box to what's displayed
        self.toolbar.source_select.currentIndexChanged[int].connect(
            lambda ind: self.load_selection(self.catalog[ind]))

    def register_to_hub(self, hub):
        super(MOSVizViewer, self).register_to_hub(hub)

        hub.subscribe(self, msg.SubsetCreateMessage,
                      handler=self._add_subset)

        hub.subscribe(self, msg.SubsetUpdateMessage,
                      handler=self._update_subset)

        hub.subscribe(self, msg.SubsetDeleteMessage,
                      handler=self._remove_subset)

        hub.subscribe(self, msg.DataUpdateMessage,
                      handler=self._update_data)

    def add_data(self, data):
        """
        Processes data message from the central communication hub.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object.
        """
        self._unpack_selection(data)
        return True

    def add_subset(self, subset):
        """
        Processes subset messages from the central communication hub.

        Parameters
        ----------
        subset :
            Subset object.
        """
        self._unpack_selection(subset)
        return True

    def _update_data(self, message):
        """
        Update data message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Data message object.
        """
        data = message.data
        # self._unpack_selection(data)

    def _add_subset(self, message):
        """
        Add subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Subset message object.
        """
        self._unpack_selection(message.subset)

    def _update_subset(self, message):
        """
        Update subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Update message object.
        """
        subset = message.subset
        self._unpack_selection(subset)

    def _remove_subset(self, message):
        """
        Remove subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Subset message object.
        """
        self._unpack_selection(message.subset)

    def _unpack_selection(self, data):
        """
        Interprets the :class:`glue.core.data.Data` object by decomposing the
        data elements, extracting relevant data, and recomposing a
        package-agnostic dictionary object containing the relevant data.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Glue data object to decompose.

        """
        mask = None

        if isinstance(data, Subset):
            try:
                mask = data.to_mask()
            except IncompatibleAttribute:
                return

            if not np.any(mask):
                return

            data = data.data

        # Clear the table
        self.catalog = Table()

        col_names = data.components

        for att in col_names:
            cid = data.id[att]
            component = data.get_component(cid)

            if component.categorical:
                comp_labels = component.labels[mask]

                if comp_labels.ndim > 1:
                    comp_labels = comp_labels[0]

                if str(att) in ['spectrum1d', 'spectrum2d', 'cutout']:
                    path = '/'.join(component._load_log.path.split('/')[:-1])
                    self.catalog[str(att)] = [os.path.join(path, x)
                                              for x in comp_labels]
                else:
                    self.catalog[str(att)] = comp_labels
            else:
                comp_data = component.data[mask]

                if comp_data.ndim > 1:
                    comp_data = comp_data[0]

                self.catalog[str(att)] = comp_data

        self._update_navigation()
        self.load_selection(self.catalog[0])

    def _update_navigation(self):
        """
        Updates the :class:`qtpy.QtWidgets.QComboBox` widget with the
        appropriate source `id`s from the MOS catalog.
        """
        self.toolbar.source_select.clear()
        self.toolbar.source_select.addItems(self.catalog['id'][:])

    def load_selection(self, row):
        """
        Processes a row in the MOS catalog by first loading the data set,
        updating the stored data components, and then rendering the data on
        the visible MOSViz viewer plots.

        Parameters
        ----------
        row : :class:`astropy.table.Row`
            A `row` object representing a row in the MOS catalog. Each key
            should be a column name.
        """
        spec1d_data = nirspec_spectrum1d_reader(row['spectrum1d'])
        spec2d_data = nirspec_spectrum2d_reader(row['spectrum2d'])

        self._update_data_components(spec1d_data)
        self._update_data_components(spec2d_data)

        self.render_data(spec1d_data, spec2d_data)

    def _update_data_components(self, data):
        """
        Update the data components that act as containers for the displayed
        data in the MOSViz viewer. This obviates the need to keep creating new
        data components.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object to replace within the component.
        key : string
            Key referencing the data stored data object.
        """
        for dc in self.session.data_collection.data:
            if dc.label == data.label:
                dc.update_values_from_data(data)
                break
        else:
            self.session.data_collection.append(data)

    def render_data(self, spec1d_data=None, spec2d_data=None,
                    image_data=None):
        """
        Render the updated data sets in the individual plot widgets within the
        MOSViz viewer.
        """
        if spec1d_data is not None:
            self.spectrum1d_widget.set_data(
                x=spec1d_data.get_component(spec1d_data.id['Wavelength']).data,
                y=spec1d_data.get_component(spec1d_data.id['Spectral Flux']).data,
                yerr=spec1d_data.get_component(spec1d_data.id['Variance']).data)

        if spec2d_data is not None:
            self.spectrum2d_widget.set_image(
                spec2d_data.get_component(
                    spec2d_data.id['Data Quality']).data)
            self.spectrum2d_widget._redraw()

        if True:
            # Random 2d image data until loaders are created
            self.image_widget.set_image(np.random.sample((100, 100)))
            self.image_widget._redraw()

    def closeEvent(self, event):
        """
        Clean up the extraneous data components created when opening the
        MOSViz viewer by overriding the parent class's close event.
        """
        super(MOSVizViewer, self).closeEvent(event)

        for data in self._loaded_data.values():
            self.session.data_collection.remove(data)




