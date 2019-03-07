import os

from qtpy import QtWidgets
from glue.external.echo import HasCallbackProperties, SelectionCallbackProperty
from glue.external.echo.qt import autoconnect_callbacks_to_qt
from glue.utils.qt import load_ui

from glue.core.data_combo_helper import ComponentIDComboHelper

from ..loaders.utils import (SPECTRUM1D_LOADERS, SPECTRUM2D_LOADERS,
                             CUTOUT_LOADERS, LEVEL2_LOADERS, split_file_name)
from .. import UI_DIR


class LoaderSelectionDialog(QtWidgets.QDialog, HasCallbackProperties):

    # The dialog has a number of combo boxes that are linked to columns/fields
    # in the data. We now define these all here and the set things up and
    # check things programmatically to avoid duplicating too much code.

    columns = [{'property': 'spectrum1d', 'default': 'spectrum1d',
                'categorical': True, 'numeric': False},
               {'property': 'spectrum2d', 'default': 'spectrum2d',
                'categorical': True, 'numeric': False},
               {'property': 'cutout', 'default': 'cutout',
                'categorical': True, 'numeric': False},
               {'property': 'level2', 'default': 'level2',
                'categorical': True, 'numeric': False},
               {'property': 'source_id', 'default': 'id',
                'categorical': True, 'numeric': False},
               {'property': 'slit_ra', 'default': 'ra',
                'categorical': False, 'numeric': True},
               {'property': 'slit_dec', 'default': 'dec',
                'categorical': False, 'numeric': True},
               {'property': 'slit_width', 'default': 'slit_width',
                'categorical': False, 'numeric': True},
               {'property': 'slit_length', 'default': 'slit_length',
                'categorical': False, 'numeric': True}]

    loader_spectrum1d = SelectionCallbackProperty()
    loader_spectrum2d = SelectionCallbackProperty()
    loader_cutout = SelectionCallbackProperty()
    loader_level2 = SelectionCallbackProperty()

    spectrum1d = SelectionCallbackProperty()
    spectrum2d = SelectionCallbackProperty()
    cutout = SelectionCallbackProperty()
    level2 = SelectionCallbackProperty()

    source_id = SelectionCallbackProperty()

    slit_ra = SelectionCallbackProperty()
    slit_dec = SelectionCallbackProperty()
    slit_width = SelectionCallbackProperty()
    slit_length = SelectionCallbackProperty()

    slit_north_aligned = SelectionCallbackProperty()

    def __init__(self, parent=None, data=None):

        QtWidgets.QDialog.__init__(self, parent=parent)

        self.data = data

        # level 2 data is optional. This flag is used throughout
        # the code to control the input and display of information
        # associated with level 2 data.
        self.is_level2 = False
        for component in data.components:
            if component.label.lower() == 'level2':
                self.is_level2 = True

        self.ui = load_ui('loader_selection.ui', self, directory=UI_DIR)

        self.setWindowTitle("Loader Selection")

        # By defult, ui is built for level 2 data. Must be
        # re-configured for level 3-only data.
        if not self.is_level2:

            # Since we are modifying self.columns below by popping one of the
            # elements, we should make a copy of the columns attribute first
            # to avoid modifying the class-level attribute for all future
            # instances
            self.columns = self.columns[:]

            self.columns.pop(3)
            self.ui.combosel_level2.hide()
            self.ui.combosel_loader_level2.hide()
            self.ui.label_14.hide()

        LoaderSelectionDialog.loader_spectrum1d.set_choices(self, sorted(SPECTRUM1D_LOADERS))
        LoaderSelectionDialog.loader_spectrum2d.set_choices(self, sorted(SPECTRUM2D_LOADERS))
        LoaderSelectionDialog.loader_cutout.set_choices(self, sorted(CUTOUT_LOADERS))
        if self.is_level2:
            LoaderSelectionDialog.loader_level2.set_choices(self, sorted(LEVEL2_LOADERS))

        if 'loaders' in data.meta:

            loaders = data.meta['loaders']

            if "spectrum1d" in loaders and loaders['spectrum1d'] in SPECTRUM1D_LOADERS:
                self.loader_spectrum1d = loaders['spectrum1d']
            if "spectrum2d" in loaders and loaders['spectrum2d'] in SPECTRUM2D_LOADERS:
                self.loader_spectrum2d = loaders['spectrum2d']
            if "cutout" in loaders and loaders['cutout'] in CUTOUT_LOADERS:
                self.loader_cutout = loaders['cutout']
            if self.is_level2:
                if "level2" in loaders and loaders['level2'] in LEVEL2_LOADERS:
                    self.loader_level2 = loaders['level2']

        if self.loader_spectrum1d is None:
            self.loader_spectrum1d = 'NIRSpec 1D Spectrum'
        if self.loader_spectrum2d is None:
            self.loader_spectrum2d = 'NIRSpec 2D Spectrum'
        if self.loader_cutout is None:
            self.loader_cutout = 'NIRCam Image'
        if self.is_level2:
            if self.loader_level2 is None:
                self.loader_level2 = 'NIRCam Level 2'

        # We set up ComponentIDComboHelper which takes care of populating the
        # combo box with the components.

        self._helpers = {}

        for column in self.columns:

            helper = ComponentIDComboHelper(self, column['property'], data=data,
                                            numeric=column['numeric'],
                                            categorical=column['categorical'])

            self._helpers[column['property']] = helper

            # Store components that appear in the combo inside the column object
            column['components'] = dict((x.label, x) for x in getattr(LoaderSelectionDialog, column['property']).get_choices(self))

        # We check whether any of the properties are already defined in the
        # Data.meta dictionary. This could happen for example if the user has
        # encoded some of these defaults in their data file (which we
        # document how to do).

        if 'special_columns' in data.meta:
            special_columns = data.meta['special_columns']
            for column in self.columns:
                if column['property'] in special_columns:
                    column_name = special_columns[column['property']]
                    if column_name in column['components']:
                        setattr(self, column['property'], column['components'][column_name])

        # We now check whether each property is not None, and if so we set it either
        # to the default, if present, or to the first component otherwise. In
        # future we could replace the default by a function that could do more
        # sophisticated auto-testing.

        for column in self.columns:
            if not column['components']:
                continue
            if getattr(self, column['property']) is not None:
                if column['default'] in column['components']:
                    setattr(self, column['property'], column['components'][column['default']])
                else:
                    setattr(self, column['property'], sorted(column['components'])[0])

        # The following is a call to a function that deals with setting up the
        # linking between the callback properties here and the Qt widgets.

        autoconnect_callbacks_to_qt(self, self.ui)

        self.button_cancel.clicked.connect(self.reject)
        self.button_ok.clicked.connect(self.accept)

        self.add_global_callback(self._validation_checks)

        self._validation_checks()

    def accept(self):

        if 'loaders' not in self.data.meta:
            self.data.meta['loaders'] = {}

        self.data.meta['loaders']['spectrum1d'] = self.loader_spectrum1d
        self.data.meta['loaders']['spectrum2d'] = self.loader_spectrum2d
        self.data.meta['loaders']['cutout'] = self.loader_cutout
        if self.is_level2:
            self.data.meta['loaders']['level2'] = self.loader_level2

        if 'special_columns' not in self.data.meta:
            self.data.meta['special_columns'] = {}

        for column in self.columns:
            attr = getattr(self, column['property'])
            self.data.meta['special_columns'][column['property']] = attr.label

        self.data.meta['loaders_confirmed'] = True

        super(LoaderSelectionDialog, self).accept()

    def _validation_checks(self, *args, **kwargs):

        # Check whether the files indicated by the filename columns do in fact
        # exist
        for column in ['spectrum1d', 'spectrum2d', 'cutout', 'level2']:

            if not self.is_level2 and column in ['level2']:
                continue

            column_name = getattr(self, column)

            filenames = self.data.get_component(column_name).labels
            path = os.sep.join(
                self.data._load_log.path.split(os.sep)[:-1])

            for filename in filenames:

                filename, ext = split_file_name(filename)

                file_path = os.path.join(path, filename)
                base = os.path.basename(file_path)
                if base != "None":
                    if not os.path.exists(file_path):
                        self.validate(False, "File '{0}' listed in column '{1}' "
                                      "(currently selected for {2}) does not "
                                      "exist.".format(filename, column_name, column))
                        return

        # Check whether the loaders are able to read in the spectra/cutouts. We
        # can't check whether all spectra/cutouts can be read since this would
        # be too computationally intensive, but we can at least check the first
        # one.

        loaders = [SPECTRUM1D_LOADERS, SPECTRUM2D_LOADERS, CUTOUT_LOADERS, LEVEL2_LOADERS]

        for column, loaders in zip(['spectrum1d', 'spectrum2d', 'cutout', 'level2'], loaders):

            if not self.is_level2 and column in ['level2']:
                continue

            loader_name = getattr(self, 'loader_' + column)
            loader = loaders[loader_name]
            column_name = getattr(self, column)
            filenames = self.data.get_component(column_name).labels
            path = os.sep.join(
                self.data._load_log.path.split(os.sep)[:-1])

            test_filename = "None"
            for filename in filenames:
                file_path = os.path.join(path, filename)
                if os.path.basename(filename) != "None":
                    test_filename = filename
                    break

            if test_filename == "None":
                continue
            try:
                loader(file_path)

                self.validate(True, "All spectra and cutout files exist and "
                              "the loaders are able to read in the first one "
                              "of each.")
            except:
                self.validate(False, "An error occurred when trying to read in "
                              "'{0}' using the loader '{1}' (see terminal for "
                              "the full error).".format(filenames[0], loader_name))
                return

    def validate(self, valid, message):
        if valid:
            self.button_ok.setEnabled(True)
            self.label_status.setStyleSheet('color: green')
        else:
            self.button_ok.setEnabled(False)
            self.label_status.setStyleSheet('color: red')
        self.label_status.setText(message)


def confirm_loaders_and_column_names(data, force=False):
    if force or not data.meta.get('loaders_confirmed', False):
        loader_selection = LoaderSelectionDialog(data=data)
        return loader_selection.exec_()
    return True


if __name__ == "__main__":

    from glue.core import Data
    from glue.utils.qt import get_qapp

    app = get_qapp()

    d = Data()
    d['spectrum1d'] = ['a', 'b', 'c']
    d['spectrum2d'] = ['d', 'e', 'f']
    d['cutout'] = ['a', 'a', 'a']
    d['level2'] = ['a', 'a', 'a']
    d['ra'] = [1, 2, 2]
    d['dec'] = [1, 2, 2]
    d['slit_width'] = [1, 2, 2]
    d['slit_length'] = [1, 2, 2]

    print(confirm_loaders_and_column_names(d))
    print(confirm_loaders_and_column_names(d))
