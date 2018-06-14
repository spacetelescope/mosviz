from __future__ import print_function, division, absolute_import

import os
from collections import OrderedDict

import numpy as np
from qtpy import compat
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton
from qtpy.uic import loadUi

from glue.core import message as msg
from glue.core import Subset
from glue.core.exceptions import IncompatibleAttribute
from glue.core.data_exporters import astropy_table
from glue.core.component import CategoricalComponent
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.utils.matplotlib import defer_draw
from glue.utils.decorators import avoid_circular
from glue.utils.qt import pick_item

from specutils.core.generic import Spectrum1DRef

from astropy.table import Table
from astropy.nddata.nduncertainty import StdDevUncertainty
from astropy import units as u
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import proj_plane_pixel_area

try:
    from specviz.external.glue.data_viewer import SpecVizViewer
except ImportError:
    SpecVizViewer = None

from ..widgets.toolbars import MOSViewerToolbar
from ..widgets.plots import Line1DWidget, MOSImageWidget, DrawableImageWidget
from ..loaders.loader_selection import confirm_loaders_and_column_names
from ..loaders.utils import SPECTRUM1D_LOADERS, SPECTRUM2D_LOADERS, CUTOUT_LOADERS
from ..widgets.viewer_options import OptionsWidget
from ..widgets.share_axis import SharedAxisHelper
from .. import UI_DIR
from ..widgets.layer_widget import SimpleLayerWidget

__all__ = ['MOSVizViewer']


class MOSVizViewer(DataViewer):

    LABEL = "MOSViz Viewer"
    window_closed = Signal()
    _toolbar_cls = MOSViewerToolbar

    def __init__(self, session, parent=None):
        super(MOSVizViewer, self).__init__(session, parent=parent)
        self.load_ui()

        # Define some data containers
        self.filepath = None
        self.savepath = None
        self.data_idx = None
        self.comments = False
        self.textChangedAt = None
        self.mask = None

        self.catalog = None
        self.current_row = None
        self._specviz_instance = None
        self._loaded_data = {}
        self._primary_data = None
        self._layer_view = SimpleLayerWidget(parent=self)
        self._layer_view.layer_combo.currentIndexChanged.connect(self._selection_changed)
        self.resize(800, 600)

    def load_ui(self):
        """
        Setup the MOSView viewer interface.
        """
        self.central_widget = QWidget(self)

        path = os.path.join(UI_DIR, 'mos_widget.ui')
        loadUi(path, self.central_widget)

        self.image_widget = DrawableImageWidget()
        self.spectrum2d_widget = MOSImageWidget()
        self.spectrum1d_widget = Line1DWidget()

        # Set up helper for sharing axes. SharedAxisHelper defaults to no sharing
        # and we control the sharing later by setting .sharex and .sharey on the
        # helper
        self.spectrum2d_spectrum1d_share = SharedAxisHelper(self.spectrum2d_widget._axes,
                                                            self.spectrum1d_widget._axes)
        self.spectrum2d_image_share = SharedAxisHelper(self.spectrum2d_widget._axes,
                                                       self.image_widget._axes)

        # We only need to set the image widget to keep the same aspect ratio
        # since the two other viewers don't require square pixels, so the axes
        # should not change shape.
        self.image_widget._axes.set_adjustable('datalim')

        self.meta_form_layout = self.central_widget.meta_form_layout
        self.meta_form_layout.setFieldGrowthPolicy(self.meta_form_layout.ExpandingFieldsGrow)
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

        # Keep the left and right splitters in sync otherwise the axes don't line up
        self.central_widget.left_vertical_splitter.splitterMoved.connect(self._left_splitter_moved)
        self.central_widget.right_vertical_splitter.splitterMoved.connect(self._right_splitter_moved)

        # Set the central widget
        self.setCentralWidget(self.central_widget)

        # Define the options widget
        self._options_widget = OptionsWidget()

    def show(self, *args, **kwargs):
        super(MOSVizViewer, self).show(*args, **kwargs)
        # Trigger a sync between the splitters
        self._left_splitter_moved()

    @avoid_circular
    def _right_splitter_moved(self, *args, **kwargs):
        sizes = self.central_widget.right_vertical_splitter.sizes()
        self.central_widget.left_vertical_splitter.setSizes(sizes)

    @avoid_circular
    def _left_splitter_moved(self, *args, **kwargs):
        sizes = self.central_widget.left_vertical_splitter.sizes()
        self.central_widget.right_vertical_splitter.setSizes(sizes)

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
        if SpecVizViewer is not None:
            self.toolbar.open_specviz.triggered.connect(
                lambda: self._open_in_specviz())
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

        def has_data_or_subset(x):
            if x.sender is self._primary_data:
                return True
            elif isinstance(x.sender, Subset) and x.sender.data is self._primary_data:
                return True
            else:
                return False

        hub.subscribe(self, msg.SubsetCreateMessage,
                      handler=self._add_subset,
                      filter=has_data_or_subset)

        hub.subscribe(self, msg.SubsetUpdateMessage,
                      handler=self._update_subset,
                      filter=has_data_or_subset)

        hub.subscribe(self, msg.SubsetDeleteMessage,
                      handler=self._remove_subset,
                      filter=has_data_or_subset)

        hub.subscribe(self, msg.DataUpdateMessage,
                      handler=self._update_data,
                      filter=has_data_or_subset)

    def add_data(self, data):
        """
        Processes data message from the central communication hub.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object.
        """

        # Check whether the data is suitable for the MOSViz viewer - basically
        # we expect a table of 1D columns with at least three string and four
        # floating-point columns.

        if data.ndim != 1:
            QMessageBox.critical(self, "Error", "MOSViz viewer can only be used "
                                 "for data with 1-dimensional components",
                                 buttons=QMessageBox.Ok)
            return False

        components = [data.get_component(cid) for cid in data.visible_components]

        categorical = [c for c in components if c.categorical]
        if len(categorical) < 3:
            QMessageBox.critical(self, "Error", "MOSViz viewer expected at least "
                                 "three string components/columns, representing "
                                 "the filenames of the 1D and 2D spectra and "
                                 "cutouts", buttons=QMessageBox.Ok)
            return False

        # We can relax the following requirement if we make the slit parameters
        # optional
        numerical = [c for c in components if c.numeric]
        if len(numerical) < 4:
            QMessageBox.critical(self, "Error", "MOSViz viewer expected at least "
                                 "four numerical components/columns, representing "
                                 "the slit position, length, and position angle",
                                 buttons=QMessageBox.Ok)
            return False

        # Make sure the loaders and column names are correct
        result = confirm_loaders_and_column_names(data)
        if not result:
            return False

        self._primary_data = data
        self._layer_view.data = data
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
        self._layer_view.refresh()
        index = self._layer_view.layer_combo.findData(subset)
        self._layer_view.layer_combo.setCurrentIndex(index)
        return True


    def _update_data(self, message):
        """
        Update data message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Data message object.
        """
        self._layer_view.refresh()

    def _add_subset(self, message):
        """
        Add subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Subset message object.
        """
        self._layer_view.refresh()

    def _update_subset(self, message):
        """
        Update subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Update message object.
        """
        self._layer_view.refresh()
        self._unpack_selection(message.subset)

    def _remove_subset(self, message):
        """
        Remove subset message.

        Parameters
        ----------
        message : :class:`glue.core.message.Message`
            Subset message object.
        """
        self._layer_view.refresh()
        self._unpack_selection(message.subset.data)

    def _selection_changed(self):
        self._unpack_selection(self._layer_view.layer_combo.currentData())

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
        self.mask = mask

        # Clear the table
        self.catalog = Table()
        self.catalog.meta = data.meta

        self.comments = False
        col_names = data.components
        for att in col_names:
            cid = data.id[att]
            component = data.get_component(cid)

            if component.categorical:
                comp_labels = component.labels[mask]

                if comp_labels.ndim > 1:
                    comp_labels = comp_labels[0]

                if str(att) in ["comments", "flag"]:
                    self.comments = True
                elif str(att) in ['spectrum1d', 'spectrum2d', 'cutout']:
                    self.filepath = component._load_log.path
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

        if len(self.catalog) > 0:
            if not self.comments:
                self.comments = self._load_comments(data.label) #Returns bool
            else:
                self._data_collection_index(data.label)
                self._get_save_path()
            # Update gui elements
            self._update_navigation(select=0)

    def _update_navigation(self, select=0):
        """
        Updates the :class:`qtpy.QtWidgets.QComboBox` widget with the
        appropriate source `id`s from the MOS catalog.
        """

        if self.toolbar is None:
            return

        self.toolbar.source_select.blockSignals(True)

        self.toolbar.source_select.clear()

        if len(self.catalog) > 0 and 'id' in self.catalog.colnames:
            self.toolbar.source_select.addItems(self.catalog['id'][:])

        self.toolbar.source_select.setCurrentIndex(select)

        self.toolbar.source_select.blockSignals(False)

        self.toolbar.source_select.currentIndexChanged.emit(select)

    def _set_navigation(self, index):

        if len(self.catalog) < index:
            return

        if 0 <= index < self.toolbar.source_select.count():
            self.toolbar.source_select.setCurrentIndex(index)

        if index <= 0:
            self.toolbar.cycle_previous_action.setDisabled(True)
        else:
            self.toolbar.cycle_previous_action.setDisabled(False)

        if index >= self.toolbar.source_select.count() - 1:
            self.toolbar.cycle_next_action.setDisabled(True)
        else:
            self.toolbar.cycle_next_action.setDisabled(False)

    def _open_in_specviz(self):
        _specviz_instance = self.session.application.new_data_viewer(
            SpecVizViewer)

        spec1d_data = self._loaded_data['spectrum1d']

        spec_data = Spectrum1DRef(
            data=spec1d_data.get_component(spec1d_data.id['Flux']).data,
            dispersion=spec1d_data.get_component(spec1d_data.id['Wavelength']).data,
            uncertainty=StdDevUncertainty(spec1d_data.get_component(spec1d_data.id['Uncertainty']).data),
            unit="", name=self.current_row['id'],
            wcs=WCS(spec1d_data.header))

        _specviz_instance.open_data(spec_data)

    def load_selection(self, row):
        """
        Processes a row in the MOS catalog by first loading the data set,
        updating the stored data components, and then rendering the data on
        the visible MOSViz viewer plots.

        Parameters
        ----------
        row : :class:`astropy.table.Row`
            A row object representing a row in the MOS catalog. Each key
            should be a column name.
        """

        self.current_row = row

        # Get loaders
        loader_spectrum1d = SPECTRUM1D_LOADERS[self.catalog.meta["loaders"]["spectrum1d"]]
        loader_spectrum2d = SPECTRUM2D_LOADERS[self.catalog.meta["loaders"]["spectrum2d"]]
        loader_cutout = CUTOUT_LOADERS[self.catalog.meta["loaders"]["cutout"]]

        # Get column names
        colname_spectrum1d = self.catalog.meta["special_columns"]["spectrum1d"]
        colname_spectrum2d = self.catalog.meta["special_columns"]["spectrum2d"]
        colname_cutout = self.catalog.meta["special_columns"]["cutout"]

        spec1d_data = loader_spectrum1d(row[colname_spectrum1d])
        spec2d_data = loader_spectrum2d(row[colname_spectrum2d])

        self._update_data_components(spec1d_data, key='spectrum1d')
        self._update_data_components(spec2d_data, key='spectrum2d')

        basename = os.path.basename(row[colname_cutout])
        if basename == "None":
            self.render_data(row, spec1d_data, spec2d_data, None)
        else:
            image_data = loader_cutout(row[colname_cutout])
            self._update_data_components(image_data, key='cutout')
            self.render_data(row, spec1d_data, spec2d_data, image_data)

    def _update_data_components(self, data, key):
        """
        Update the data components that act as containers for the displayed
        data in the MOSViz viewer. This obviates the need to keep creating new
        data components.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object to replace within the component.
        key : str
            References the particular data set type.
        """
        cur_data = self._loaded_data.get(key, None)

        if cur_data is None:
            self._loaded_data[key] = data
            self.session.data_collection.append(data)
        else:
            cur_data.update_values_from_data(data)

    def render_data(self, row, spec1d_data=None, spec2d_data=None,
                    image_data=None):
        """
        Render the updated data sets in the individual plot widgets within the
        MOSViz viewer.
        """
        self._check_unsaved_comments()

        if spec1d_data is not None:

            spectrum1d_x = spec1d_data[spec1d_data.id['Wavelength']]
            spectrum1d_y = spec1d_data[spec1d_data.id['Flux']]
            spectrum1d_yerr = spec1d_data[spec1d_data.id['Uncertainty']]

            self.spectrum1d_widget.set_data(x=spectrum1d_x,
                                            y=spectrum1d_y,
                                            yerr=spectrum1d_yerr)

            # Try to retrieve the wcs information
            try:
                flux_unit = spec1d_data.header.get('BUNIT', 'Jy').lower()
                flux_unit = flux_unit.replace('counts', 'count')
                flux_unit = u.Unit(flux_unit)
            except ValueError:
                flux_unit = u.Unit("Jy")

            try:
                disp_unit = spec1d_data.header.get('CUNIT1', 'Angstrom').lower()
                disp_unit = u.Unit(disp_unit)
            except ValueError:
                disp_unit = u.Unit("Angstrom")

            self.spectrum1d_widget.axes.set_xlabel("Wavelength [{}]".format(disp_unit))
            self.spectrum1d_widget.axes.set_ylabel("Flux [{}]".format(flux_unit))

        if image_data is not None:
            wcs = image_data.coords.wcs

            self.image_widget.set_image(image_data.get_component(image_data.id['Flux']).data,
                                        wcs=wcs, interpolation='none', origin='lower')

            self.image_widget.axes.set_xlabel("Spatial X")
            self.image_widget.axes.set_ylabel("Spatial Y")

            # Add the slit patch to the plot

            ra = row[self.catalog.meta["special_columns"]["slit_ra"]] * u.degree
            dec = row[self.catalog.meta["special_columns"]["slit_dec"]] * u.degree
            slit_width = row[self.catalog.meta["special_columns"]["slit_width"]]
            slit_length = row[self.catalog.meta["special_columns"]["slit_length"]]

            skycoord = SkyCoord(ra, dec, frame='fk5')
            xp, yp = skycoord.to_pixel(wcs)

            scale = np.sqrt(proj_plane_pixel_area(wcs)) * 3600.

            dx = slit_width / scale
            dy = slit_length / scale

            self.image_widget.draw_rectangle(x=xp, y=yp,
                                             width=dx, height=dy)

            self.image_widget._redraw()
        else:
            self.image_widget.setVisible(False)

        # Plot the 2D spectrum data last because by then we can make sure that
        # we set up the extent of the image appropriately if the cutout and the
        # 1D spectrum are present so that the axes can be locked.

        if spec2d_data is not None:
            wcs = spec2d_data.coords.wcs

            xp2d = np.arange(spec2d_data.shape[1])
            yp2d = np.repeat(0, spec2d_data.shape[1])
            spectrum2d_disp, spectrum2d_offset = spec2d_data.coords.pixel2world(xp2d, yp2d)
            x_min = spectrum2d_disp.min()
            x_max = spectrum2d_disp.max()

            if image_data is None:
                y_min = -0.5
                y_max = spec2d_data.shape[0] - 0.5
            else:
                y_min = yp - dy / 2.
                y_max = yp + dy / 2.

            extent = [x_min, x_max, y_min, y_max]

            self.spectrum2d_widget.set_image(
                image=spec2d_data.get_component(
                    spec2d_data.id['Flux']).data,
                interpolation='none', aspect='auto',
                extent=extent, origin='lower')

            self.spectrum2d_widget.axes.set_xlabel("Wavelength")
            self.spectrum2d_widget.axes.set_ylabel("Spatial Y")

            self.spectrum2d_widget._redraw()

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
            if col.lower() not in ["comments", "flag"]:
                line_edit = QLineEdit(str(row[col]),
                                      self.central_widget.meta_form_widget)
                line_edit.setReadOnly(True)

                self.meta_form_layout.addRow(col, line_edit)

        # Set up comment and flag input/display boxes
        if self.comments:
            if self.savepath is not None:
                if self.savepath == -1:
                    line_edit = QLineEdit(os.path.basename("Not Saving to File."),
                                      self.central_widget.meta_form_widget)
                    line_edit.setReadOnly(True)
                    self.meta_form_layout.addRow("Save File", line_edit)
                else:
                    line_edit = QLineEdit(os.path.basename(self.savepath),
                                      self.central_widget.meta_form_widget)
                    line_edit.setReadOnly(True)
                    self.meta_form_layout.addRow("Save File", line_edit)

            self.input_flag = QLineEdit(self.get_flag(),
                self.central_widget.meta_form_widget)
            self.input_flag.textChanged.connect(self._text_changed)
            self.input_flag.setStyleSheet("background-color: rgba(255, 255, 255);")
            self.meta_form_layout.addRow("Flag", self.input_flag)

            self.input_comments = QPlainTextEdit(self.get_comment(),
                self.central_widget.meta_form_widget)
            self.input_comments.textChanged.connect(self._text_changed)
            self.input_comments.setStyleSheet("background-color: rgba(255, 255, 255);")
            self.meta_form_layout.addRow("Comments", self.input_comments)

            self.input_save = QPushButton('Save',
                self.central_widget.meta_form_widget)
            self.input_save.clicked.connect(self.update_comments)
            self.input_save.setDefault(True)

            self.input_refresh = QPushButton('Reload',
                self.central_widget.meta_form_widget)
            self.input_refresh.clicked.connect(self.refresh_comments)

            self.meta_form_layout.addRow(self.input_save, self.input_refresh)


    @defer_draw
    def set_locked_axes(self, x=None, y=None):

        # Here we only change the setting if x or y are not None
        # since if set_locked_axes is called with eg. x=True, then
        # we shouldn't change the y setting.

        if x is not None:
            self.spectrum2d_spectrum1d_share.sharex = x

        if y is not None:
            self.spectrum2d_image_share.sharey = y

        self.spectrum1d_widget._redraw()
        self.spectrum2d_widget._redraw()
        self.image_widget._redraw()

    def layer_view(self):
        return self._layer_view

    def _text_changed(self):
        if self.textChangedAt is None:
            i = self.toolbar.source_select.currentIndex()
            self.textChangedAt = self._index_hash(i)

    def _check_unsaved_comments(self):
        if self.textChangedAt is None:
            return #Nothing to be changed
        i = self.toolbar.source_select.currentIndex()
        i = self._index_hash(i)
        if self.textChangedAt == i:
            self.textChangedAt = None
            return #This is a refresh
        info = "Comments or flags changed but were not saved. Would you like to save them?"
        reply = QMessageBox.question(self, '', info, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.update_comments(True)
        self.textChangedAt = None

    def _data_collection_index(self, label):
        idx = -1
        for i, l in enumerate(self.session.data_collection):
            if l.label == label:
                idx = i
                break
        if idx == -1:
            return -1
        self.data_idx = idx
        return idx

    def _index_hash(self, i):
        """Local selection index -> Table index"""
        if self.mask is not None:
            size = self.mask.size
            temp = np.arange(size)
            return temp[self.mask][i]
        else:
            return i

    def _id_to_index_hash(self, ID, l):
        """Object Name -> Table index"""
        for i, name in enumerate(l):
            if name == ID:
                return i
        return None

    def get_comment(self):
        idx = self.data_idx
        i = self.toolbar.source_select.currentIndex()
        i = self._index_hash(i)
        comp = self.session.data_collection[idx].get_component("comments")
        return comp._categorical_data[i]

    def get_flag(self):
        idx = self.data_idx
        i = self.toolbar.source_select.currentIndex()
        i = self._index_hash(i)
        comp = self.session.data_collection[idx].get_component("flag")
        return comp._categorical_data[i]

    def send_NumericalDataChangedMessage(self):
        idx = self.data_idx
        data = self.session.data_collection[idx]
        data.hub.broadcast(msg.NumericalDataChangedMessage(data, "comments"))

    def refresh_comments(self):
        self.input_flag.setText(self.get_flag())
        self.input_comments.setPlainText(self.get_comment())
        self.input_flag.setStyleSheet("background-color: rgba(255, 255, 255);")
        self.textChangedAt = None

    def _get_save_path(self):
        """
        Try to get save path from other MOSVizViewer instances
        """
        for v in self.session.application.viewers[0]:
            if isinstance(v, MOSVizViewer):
                if v.savepath is not None:
                    if v.data_idx == self.data_idx:
                        self.savepath = v.savepath
                        break

    def _setup_save_path(self):
        """
        Prompt the user for a file to save comments and flags into.
        """
        fail = True
        success = False
        info = "Where would you like to save comments and flags?"
        option = pick_item([0, 1],
            [os.path.basename(self.filepath), "New MOSViz Table file"],
            label=info,  title="Comment Setup")
        if option == 0:
            self.savepath = self.filepath
        elif option == 1:
            dirname = os.path.dirname(self.filepath)
            path = compat.getsavefilename(caption="New MOSViz Table File",
                basedir=dirname, filters="*.txt")[0]
            if path == "":
                return fail
            self.savepath = path
        else:
            return fail

        for v in self.session.application.viewers[0]:
            if isinstance(v, MOSVizViewer):
                if v.data_idx == self.data_idx:
                    v.savepath = self.savepath
        self._layer_view.refresh()
        return success

    def update_comments(self, pastSelection = False):
        """
        Process comment and flag changes and save to file.

        Parameters
        ----------
        pastSelection : bool
            True when updating past selections. Used when
            user forgets to save.
        """
        if self.input_flag.text() == "":
            self.input_flag.setStyleSheet("background-color: rgba(255, 0, 0);")
            return

        i = None
        try:
            i = int(self.input_flag.text())
        except ValueError:
            self.input_flag.setStyleSheet("background-color: rgba(255, 0, 0);")
            info = QMessageBox.information(self, "Status:", "Flag must be an int!")
            return
        self.input_flag.setStyleSheet("background-color: rgba(255, 255, 255);")

        idx = self.data_idx
        if pastSelection:
            i = self.textChangedAt
            self.textChangedAt = None
        else:
            i = self.toolbar.source_select.currentIndex()
            i = self._index_hash(i)
        data = self.session.data_collection[idx]

        comp = data.get_component("comments")
        comp._categorical_data.flags.writeable = True
        comp._categorical_data[i] = self.input_comments.toPlainText()

        comp = data.get_component("flag")
        comp._categorical_data.flags.writeable = True
        comp._categorical_data[i] = self.input_flag.text()

        self.send_NumericalDataChangedMessage()
        self.write_comments()

        self.textChangedAt = None

    def _load_comments(self, label):
        """
        Populate the comments and flag columns.
        Attempt to load comments from file.

        Parameters
        ----------
        label : str
            The label of the data in
            session.data_collection.
        """

        #Make sure its the right data
        #(beacuse subset data is masked)
        idx = self._data_collection_index(label)
        if idx == -1:
            return False
        data = self.session.data_collection[idx]

        #Fill in default comments:
        length = data.shape[0]
        new_comments = np.array(["" for i in range(length)], dtype=object)
        new_flags = np.array(["0" for i in range(length)], dtype=object)

        #Fill in any saved comments:
        meta = data.meta
        obj_names = data.get_component("id")._categorical_data

        if "MOSViz_comments" in meta.keys():
            try:
                comments = meta["MOSViz_comments"]
                for key in comments.keys():
                    index = self._id_to_index_hash(key, obj_names)
                    if index is not None:
                        line = comments[key]
                        new_comments[index] = line
            except Exception as e:
                print("MOSViz Comment Load Failed: ", e)

        if "MOSViz_flags" in meta.keys():
            try:
                flags = meta["MOSViz_flags"]
                for key in flags.keys():
                    index = self._id_to_index_hash(key, obj_names)
                    if index is not None:
                        line = flags[key]
                        new_flags[index] = line
            except Exception as e:
                print("MOSViz Flag Load Failed: ", e)

        #Send to DC
        data.add_component(CategoricalComponent(new_flags, "flag"), "flag")
        data.add_component(CategoricalComponent(new_comments, "comments"), "comments")
        return True

    def write_comments(self):
        """
        Setup save file. Write comments and flags to file
        """

        if self.savepath is None:
            fail = self._setup_save_path()
            if fail: return
        if self.savepath == -1:
            return #Do not save to file option

        idx = self.data_idx
        data = self.session.data_collection[idx]
        save_comments = data.get_component("comments")._categorical_data
        save_flag = data.get_component("flag")._categorical_data
        obj_names = data.get_component("id")._categorical_data

        fn = self.savepath
        folder = os.path.dirname(fn)

        t = astropy_table.data_to_astropy_table(data)

        #Check if load and save dir paths match
        temp = os.path.dirname(self.filepath)
        if not  os.path.samefile(folder, temp):
            t['spectrum1d'].flags.writeable = True
            t['spectrum2d'].flags.writeable = True
            t['cutout'].flags.writeable = True
            for i in range(len(t)):
                t['spectrum1d'][i] = os.path.abspath(t['spectrum1d'][i])
                t['spectrum2d'][i] = os.path.abspath(t['spectrum2d'][i])
                t['cutout'][i] = os.path.abspath(t['cutout'][i])
        try:
            t.remove_column("comments")
            t.remove_column("flag")

            keys = t.meta.keys()

            if "MOSViz_comments" in keys:
                t.meta.pop("MOSViz_comments")

            if "MOSViz_flags" in keys:
                t.meta.pop("MOSViz_flags")

            comments = OrderedDict()
            flags = OrderedDict()

            for i, line in enumerate(save_comments):
                if line != "":
                    line = line.replace("\n", " ")
                    key = str(obj_names[i])
                    comments[key] = line

            for i, line in enumerate(save_flag):
                if line != "0" and line != "":
                    line = com.replace("\n", " ")
                    key = str(obj_names[i])
                    flags[key] = line

            if len(comments) > 0:
                t.meta["MOSViz_comments"] = comments
            if len(flags) > 0:
                t.meta["MOSViz_flags"] = flags

            t.write(fn, format="ascii.ecsv", overwrite=True)
        except Exception as e:
            print("Comment write failed:", e)

    def closeEvent(self, event):
        """
        Clean up the extraneous data components created when opening the
        MOSViz viewer by overriding the parent class's close event.
        """
        super(MOSVizViewer, self).closeEvent(event)

        for data in self._loaded_data.values():
            self.session.data_collection.remove(data)
