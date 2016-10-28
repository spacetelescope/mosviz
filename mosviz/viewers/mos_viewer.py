import os

from glue.qt.widgets.data_viewer import DataViewer
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLineEdit
from qtpy.uic import loadUi

from ..widgets.toolbars import MOSViewerToolbar
from ..widgets.plots import Line1DWidget, ShareableAxesImageWidget, DrawableImageWidget
from ..loaders import mos_loaders
from ..widgets.viewer_options import OptionsWidget

from glue import config
from glue.core import message as msg
from glue.core import Subset
from glue.core.exceptions import IncompatibleAttribute
from astropy.table import Table

try:
    from specviz.external.glue.data_viewer import SpecvizViewer
except ImportError:
    SpecvizViewer = None


class MOSVizViewer(DataViewer):
    LABEL = "MosViz Viewer"
    window_closed = Signal()
    _toolbar_cls = MOSViewerToolbar

    def __init__(self, session, parent=None):
        super(MOSVizViewer, self).__init__(session, parent=parent)
        self.load_ui()

        # Define some data containers
        self.catalog = None
        self._specviz_instance = None

    def load_ui(self):
        """
        Setup the MOSView viewer interface.
        """
        self.central_widget = QWidget()

        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'widgets', 'ui', 'mos_widget.ui'))
        loadUi(path, self.central_widget)

        self.image_widget = DrawableImageWidget()
        self.spectrum2d_widget = ShareableAxesImageWidget()
        self.spectrum1d_widget = Line1DWidget()
        self.meta_form_layout = self.central_widget.meta_form_layout

        self.central_widget.left_vertical_splitter.insertWidget(0, self.image_widget)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum2d_widget)
        self.central_widget.right_vertical_splitter.addWidget(self.spectrum1d_widget)

        # Set the splitter stretch factors
        self.central_widget.left_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.left_vertical_splitter.setStretchFactor(1, 8)

        self.central_widget.right_vertical_splitter.setStretchFactor(0, 1)
        self.central_widget.right_vertical_splitter.setStretchFactor(1, 2)

        self.central_widget.horizontal_splitter.setStretchFactor(0, 1)
        self.central_widget.horizontal_splitter.setStretchFactor(1, 2)

        # Set the central widget
        self.setCentralWidget(self.central_widget)

        # Define the options widget
        self._options_widget = OptionsWidget()

    def setup_connections(self):
        """
        Connects gui elements to event calls.
        """
        # Connect the selection event for the combo box to what's displayed
        self.toolbar.source_select.currentIndexChanged[int].connect(
            lambda ind: self.load_selection(self.catalog[ind]))

        self.toolbar.source_select.currentIndexChanged[int].connect(
            lambda ind: self._set_navigation(ind))

        # Connect the specviz button
        if SpecvizViewer is not None:
            self.toolbar.open_specviz.triggered.connect(
                lambda: self._open_in_specviz(
                    self.catalog[self.toolbar.source_select.currentIndex()]))
        else:
            self.toolbar.open_specviz.setDisabled(True)

        # Connect previous and forward buttons
        self.toolbar.cycle_next_action.triggered.connect(
            lambda: self._set_navigation(
                self.toolbar.source_select.currentIndex() + 1))

        # Connect previous and previous buttons
        self.toolbar.cycle_previous_action.triggered.connect(
            lambda: self._set_navigation(
                self.toolbar.source_select.currentIndex() - 1))

        # Connect the toolbar axes setting actions
        self.toolbar.lock_x_action.triggered.connect(
            lambda state: self.set_locked_axes(x=state))

        self.toolbar.lock_y_action.triggered.connect(
            lambda state: self.set_locked_axes(y=state))

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

        self.setup_connections()

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
        self.catalog.meta = data.meta

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

        # Update gui elements
        self._update_navigation()
        self._set_navigation(0)

        # Load the first source in the catalog
        self.load_selection(self.catalog[0])

    def _update_navigation(self):
        """
        Updates the :class:`qtpy.QtWidgets.QComboBox` widget with the
        appropriate source `id`s from the MOS catalog.
        """
        self.toolbar.source_select.clear()
        self.toolbar.source_select.addItems(self.catalog['id'][:])

    def _set_navigation(self, index):
        if 0 <= index < self.toolbar.source_select.count():
            self.toolbar.source_select.setCurrentIndex(index)
            self.load_selection(self.catalog[index])

        if index <= 0:
            self.toolbar.cycle_previous_action.setDisabled(True)
        else:
            self.toolbar.cycle_previous_action.setDisabled(False)

        if index >= self.toolbar.source_select.count() - 1:
            self.toolbar.cycle_next_action.setDisabled(True)
        else:
            self.toolbar.cycle_next_action.setDisabled(False)

    def _open_in_specviz(self, row):
        if self._specviz_instance is None:
            self._specviz_instance = self.session.application.new_data_viewer(
                SpecvizViewer)

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

        if "loaders" in self.catalog.meta:
            # if loader is specified
            if "spec1d" in self.catalog.meta["loaders"]:
                # check .glue/config.py for custom loaders
                if hasattr(config, self.catalog.meta["loaders"]["spec1d"]):
                    spectrum1d_loader = getattr(config, self.catalog.meta["loaders"]["spec1d"])

                # check built-in loaders
                else:
                    spectrum1d_loader = getattr(mos_loaders, self.catalog.meta["loaders"]["spec1d"])

            # Use the NIRSpec loader by default.
            else:
                spectrum1d_loader = mos_loaders.nirspec_spectrum1d_reader


            if "spec2d" in self.catalog.meta["loaders"]:
                if hasattr(config, self.catalog.meta["loaders"]["spec2d"]):
                    spectrum2d_loader = getattr(config, self.catalog.meta["loaders"]["spec2d"])
                else:
                    spectrum2d_loader = getattr(mos_loaders, self.catalog.meta["loaders"]["spec2d"])
            else:
                spectrum2d_loader = mos_loaders.nirspec_spectrum2d_reader

            if "image" in self.catalog.meta["loaders"]:
                if hasattr(config, self.catalog.meta["loaders"]["image"]):
                    cutout_loader = getattr(config, self.catalog.meta["loaders"]["image"])
                else:
                    cutout_loader = getattr(mos_loaders, self.catalog.meta["loaders"]["image"])

            # Use the ACS cutout loader by default.
            else:
                cutout_loader = mos_loaders.acs_cutout_image_reader
        else:
            spectrum1d_loader = mos_loaders.nirspec_spectrum1d_reader
            spectrum2d_loader = mos_loaders.nirspec_spectrum2d_reader
            cutout_loader = mos_loaders.acs_cutout_image_reader

        spec1d_data = spectrum1d_loader(row['spectrum1d'])
        spec2d_data = spectrum2d_loader(row['spectrum2d'])
        image_data = cutout_loader(row['cutout'])


        self._update_data_components(spec1d_data)
        self._update_data_components(spec2d_data)
        self._update_data_components(image_data)

        self.render_data(row, spec1d_data, spec2d_data, image_data)

    def _update_data_components(self, data):
        """
        Update the data components that act as containers for the displayed
        data in the MOSViz viewer. This obviates the need to keep creating new
        data components.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object to replace within the component.
        """
        for dc in self.session.data_collection.data:
            if dc.label == data.label:
                dc.update_values_from_data(data)
                break
        else:
            self.session.data_collection.append(data)

    def render_data(self, row, spec1d_data=None, spec2d_data=None,
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

            self.spectrum1d_widget.axes.set_xlabel("Wavelength")
            self.spectrum1d_widget.axes.set_ylabel("Flux")

        if spec2d_data is not None:
            wcs = spec2d_data.coords.wcs

            self.spectrum2d_widget.set_image(
                image=spec2d_data.get_component(
                    spec2d_data.id['Spectral Flux']).data,
                wcs=wcs, interpolation='none', aspect='auto')

            self.spectrum2d_widget.axes.set_xlabel("Wavelength")
            self.spectrum2d_widget.axes.set_ylabel("Spatial Y")

            self.spectrum2d_widget._redraw()

        if image_data is not None:
            wcs = image_data.coords.wcs

            self.image_widget.set_image(
                image_data.get_component(
                    image_data.id['Signal']).data, wcs=wcs,
                interpolation='none')

            self.image_widget.axes.set_xlabel("Spatial X")
            self.image_widget.axes.set_ylabel("Spatial Y")

            # Add the slit patch to the plot
            self.image_widget.draw_shapes(width=row['slit_width'],
                                          length=row['slit_length'])

            self.image_widget._redraw()

        # Clear the meta information widget
        # NOTE: this process is inefficient
        for i in range(self.meta_form_layout.count()):
            wid = self.meta_form_layout.itemAt(i).widget()
            label = self.meta_form_layout.labelForField(wid)

            if label is not None:
                label.deleteLater()

            wid.deleteLater()

        # Repopulate the form layout
        # NOTE: this process is inefficient
        for col in row.colnames:
            line_edit = QLineEdit(str(row[col]),
                                  self.central_widget.meta_form_widget)
            line_edit.setReadOnly(True)

            self.meta_form_layout.addRow(col, line_edit)

    def set_locked_axes(self, x=None, y=None):
        self.spectrum2d_widget.set_locked_axes(
            sharex=self.spectrum1d_widget.axes if x else x,
            sharey=self.image_widget.axes if y else y)

        self.spectrum2d_widget._redraw()
        self.image_widget._redraw()
        self.spectrum1d_widget._redraw()

    def closeEvent(self, event):
        """
        Clean up the extraneous data components created when opening the
        MOSViz viewer by overriding the parent class's close event.
        """
        super(MOSVizViewer, self).closeEvent(event)

        for data in self._loaded_data.values():
            self.session.data_collection.remove(data)




