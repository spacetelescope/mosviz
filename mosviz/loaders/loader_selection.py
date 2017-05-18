import os
from itertools import repeat

from qtpy import QtWidgets
from glue.external.echo import HasCallbackProperties, CallbackProperty
from glue.external.echo.qt import autoconnect_callbacks_to_qt
from glue.utils.qt import load_ui, update_combobox

from mosviz.loaders.mos_loaders import (SPECTRUM1D_LOADERS, SPECTRUM2D_LOADERS, CUTOUT_LOADERS)


class LoaderSelectionDialog(QtWidgets.QDialog, HasCallbackProperties):

    loader_spectrum1d = CallbackProperty()
    loader_spectrum2d = CallbackProperty()
    loader_cutout = CallbackProperty()

    colname_spectrum1d = CallbackProperty()
    colname_spectrum2d = CallbackProperty()
    colname_cutout = CallbackProperty()

    def __init__(self, parent=None, data=None):

        QtWidgets.QDialog.__init__(self, parent=parent)

        self.ui = load_ui('loader_selection.ui', self, directory=os.path.dirname(__file__))

        update_combobox(self.ui.combotext_loader_spectrum1d, zip(SPECTRUM1D_LOADERS, repeat(None)))
        update_combobox(self.ui.combotext_loader_spectrum2d, zip(SPECTRUM2D_LOADERS, repeat(None)))
        update_combobox(self.ui.combotext_loader_cutout, zip(CUTOUT_LOADERS, repeat(None)))

        components = [cid.label for cid in data.visible_components]

        update_combobox(self.ui.combotext_colname_spectrum1d, zip(components, components))
        update_combobox(self.ui.combotext_colname_spectrum2d, zip(components, components))
        update_combobox(self.ui.combotext_colname_cutout, zip(components, components))

        if 'loaders' in data.meta:

            loaders = data.meta['loaders']

            if "spec1d" in loaders and loaders['spec1d'] in SPECTRUM1D_LOADERS:
                self.loader_spectrum1d = loaders['spec1d']
            if "spec2d" in loaders and loaders['spec2d'] in SPECTRUM2D_LOADERS:
                self.loader_spectrum2d = loaders['spec2d']
            if "image" in loaders and loaders['image'] in CUTOUT_LOADERS:
                self.loader_cutout = loaders['image']

        if self.loader_spectrum1d is None:
            self.loader_spectrum1d = 'NIRSpec 1D Spectrum'
        if self.loader_spectrum2d is None:
            self.loader_spectrum2d = 'NIRSpec 2D Spectrum'
        if self.loader_cutout is None:
            self.loader_cutout = 'NIRCam Image'

        if 'special_columns' in data.meta:

            special_columns = data.meta['special_columns']

            if 'spec1d' in special_columns:
                self.colname_spectrum1d = special_columns['spec1d']
            if 'spec2d' in special_columns:
                self.colname_spectrum2d = special_columns['spec2d']
            if 'image' in special_columns:
                self.colname_cutout = special_columns['image']

        if self.colname_spectrum1d is None:
            if 'spectrum1d' in components:
                self.colname_spectrum1d = 'spectrum1d'
            else:
                self.colname_spectrum1d = components[0]
        if self.colname_spectrum2d is None:
            if 'spectrum2d' in components:
                self.colname_spectrum2d = 'spectrum2d'
            else:
                self.colname_spectrum2d = components[0]
        if self.colname_cutout is None:
            if 'cutout' in components:
                self.colname_cutout = 'cutout'
            else:
                self.colname_cutout = components[0]

        autoconnect_callbacks_to_qt(self, self.ui)

        self.data = data

    def accept(self):

        if 'loaders' not in self.data.meta:
            self.data.meta['loaders'] = {}

        self.data.meta['loaders']['spec1d'] = self.loader_spectrum1d
        self.data.meta['loaders']['spec2d'] = self.loader_spectrum2d
        self.data.meta['loaders']['image'] = self.loader_cutout

        if 'special_columns' not in self.data.meta:
            self.data.meta['special_columns'] = {}

        self.data.meta['special_columns']['spec1d'] = self.colname_spectrum1d
        self.data.meta['special_columns']['spec2d'] = self.colname_spectrum2d
        self.data.meta['special_columns']['image'] = self.colname_cutout

        super(LoaderSelectionDialog, self).accept()


def confirm_loaders_and_column_names(data):
    loader_selection = LoaderSelectionDialog(data=data)
    loader_selection.exec_()
    return data


if __name__ == "__main__":

    from glue.core import Data
    from glue.utils.qt import get_qapp

    app = get_qapp()

    d = Data()
    d['spectrum1d'] = [1, 2, 3]
    d['spectrum2d'] = [4, 5, 5]
    d['b'] = [1, 2, 2]
    d['cutout'] = [1, 1, 1]

    print(confirm_loaders_and_column_names(d))
    print(confirm_loaders_and_column_names(d))
