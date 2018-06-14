from qtpy import QtWidgets
from glue.utils.qt import update_combobox, load_ui

from .. import UI_DIR

__all__ = ['SimpleLayerWidget']


class SimpleLayerWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(SimpleLayerWidget, self).__init__(parent=parent)
        self.ui = load_ui('layer_widget.ui', self, directory=UI_DIR)
        self.data = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        if value is None:
            self.layer_text.setText("Current dataset: None")
        else:
            self.layer_text.setText("Current dataset: {0}".format(value.label))
        self.refresh()

    def refresh(self):

        if self.data is None:
            self.layer_combo.clear()
            self.layer_combo.setEnabled(False)
            return

        self.layer_combo.setEnabled(True)

        # Set up contents of combo box
        labeldata = []

        # First include the dataset itself
        labeldata.append(('Full dataset', self.data))

        for subset in self.data.subsets:
            labeldata.append((subset.label, subset))

        update_combobox(self.layer_combo, labeldata)


if __name__ == "__main__":

    from glue.utils.qt import get_qapp
    from glue.core import Data, DataCollection

    data_collection = DataCollection()
    data = Data(x=[1, 2, 3], label='banana')
    data_collection.append(data)
    data_collection.new_subset_group('a', data.id['x'] > 0)

    app = get_qapp()
    widget = SimpleLayerWidget()
    widget.show()
    widget.data = data
    app.exec_()
