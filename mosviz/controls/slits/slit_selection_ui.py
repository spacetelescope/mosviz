import os
import yaml

import astropy.units as u
from qtpy.QtWidgets import (QDialog, QLineEdit, QLabel, QComboBox,
                            QHBoxLayout, QVBoxLayout, QPushButton)

from glue.utils.qt import update_combobox


class SlitSelectionUI(QDialog):
    """
    Custom slit selection UI and editor.
    Right now it only applies slits temporarly,
    ie. if the current target is changed, slit settings
    will be lost.
    """
    def __init__(self, mosviz_viewer, parent=None):
        super(SlitSelectionUI, self).__init__(parent=parent)

        self.mosviz_viewer = mosviz_viewer
        self._slit_dict = {}

        self._mosviz_table_option_text = 'Slit from MOSViz Table'

        self._init_ui()

    def _init_ui(self):
        self.slit_type_label = QLabel('Slit Type')
        self.slit_type_combo = QComboBox()
        self.slit_type_combo.currentIndexChanged.connect(self.update_info)

        hbl1 = QHBoxLayout()
        hbl1.addWidget(self.slit_type_label)
        hbl1.addWidget(self.slit_type_combo)

        self.slit_width_label = QLabel('Slit Width')
        self.slit_width_input = QLineEdit()
        self.slit_width_combo = QComboBox()
        self.slit_width_units = QLabel('arcsec')

        hbl2 = QHBoxLayout()
        hbl2.addWidget(self.slit_width_label)
        hbl2.addWidget(self.slit_width_input)
        hbl2.addWidget(self.slit_width_combo)
        hbl2.addWidget(self.slit_width_units)

        self.slit_length_label = QLabel('Slit Length')
        self.slit_length_input = QLineEdit()
        self.slit_length_combo = QComboBox()
        self.slit_length_units = QLabel('arcsec')

        hbl3 = QHBoxLayout()
        hbl3.addWidget(self.slit_length_label)
        hbl3.addWidget(self.slit_length_input)
        hbl3.addWidget(self.slit_length_combo)
        hbl3.addWidget(self.slit_length_units)

        self.okButton = QPushButton('Apply')
        self.okButton.clicked.connect(self.apply)
        self.okButton.setDefault(True)

        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancel)

        hbl4 = QHBoxLayout()
        hbl4.addWidget(self.cancelButton)
        hbl4.addWidget(self.okButton)

        vbl = QVBoxLayout()
        vbl.addLayout(hbl1)
        vbl.addLayout(hbl2)
        vbl.addLayout(hbl3)
        vbl.addLayout(hbl4)
        self.setLayout(vbl)
        self.vbl = vbl

        self._load_selections()
        self._populate_combo()
        self.update_info(0)

        self.show()

    def _load_selections(self):
        """Load preconfigured slit shapes from yaml file"""
        file_path = os.path.join(os.path.dirname(__file__), 'saved_slits.yaml')
        with open(file_path) as f:
            self.slit_dict = yaml.load(f)

    def _populate_combo(self, default_index=0):
        """Populate combo box with slit types"""
        name_list = [self._mosviz_table_option_text] + \
                    [self.slit_dict[s]['name'] for s in sorted(self.slit_dict)] + \
                    ['Custom']

        key_list = ['default'] + [s for s in sorted(self.slit_dict)] + ['custom']

        combo_input = [(name, key) for name, key in zip(name_list, key_list)]
        update_combobox(self.slit_type_combo, combo_input, default_index=default_index)

    @property
    def width(self):
        if self.slit_width_combo.isVisible():
            width = self.slit_width_combo.currentData()
        else:
            width = self.slit_width_input.text()
        return u.Quantity(width)

    @property
    def length(self):
        if self.slit_length_combo.isVisible():
            length = self.slit_length_combo.currentData()
        else:
            length = self.slit_length_input.text()
        return u.Quantity(length)

    @property
    def width_units(self):
        return u.Unit(self.slit_width_units.text())

    @property
    def length_units(self):
        return u.Unit(self.slit_length_units.text())

    def update_info(self, index):
        """
        Update width and hight based on combo index.
        Callback for combo box.
        """
        key = self.slit_type_combo.currentData()

        length = width = None
        width_units = length_units = ''
        if key == 'default':
            slit_info = self.mosviz_viewer.get_slit_dimensions_from_file()
            width_units, length_units = self.mosviz_viewer.get_slit_units_from_file()
            if slit_info is None:
                length, width = ['N/A', 'N/A']
            else:
                length, width = slit_info
        elif key != 'custom':
            if 'length' in self.slit_dict[key]:
                length = self.slit_dict[key]['length']
            if 'width' in self.slit_dict[key]:
                width = self.slit_dict[key]['width']
        else:
            width_units = length_units = 'arcsec'

        for input_widget in [self.slit_width_input, self.slit_length_input]:
            input_widget.setStyleSheet("")

        if isinstance(width, list):
            self.slit_width_input.hide()
            self.slit_width_combo.show()
            combo_input = [(str(i), str(i)) for i in width]
            update_combobox(self.slit_width_combo, combo_input)
        elif width is None:
            self.slit_width_combo.hide()
            self.slit_width_input.show()
            self.slit_width_input.setText('')
            self.slit_width_input.setDisabled(False)
        else:
            self.slit_width_combo.hide()
            self.slit_width_input.show()
            self.slit_width_input.setText(str(width))
            self.slit_width_input.setDisabled(True)
        self.slit_width_units.setText(width_units)

        if isinstance(length, list):
            self.slit_length_input.hide()
            self.slit_length_combo.show()
            combo_input = [(str(i), str(i)) for i in length]
            update_combobox(self.slit_length_combo, combo_input)
        elif length is None:
            self.slit_length_combo.hide()
            self.slit_length_input.show()
            self.slit_length_input.setText('')
            self.slit_length_input.setDisabled(False)
        else:
            self.slit_length_combo.hide()
            self.slit_length_input.show()
            self.slit_length_input.setText(str(length))
            self.slit_length_input.setDisabled(True)
        self.slit_length_units.setText(length_units)

    def input_validation(self):
        red = "background-color: rgba(255, 0, 0, 128);"
        success = True

        for input_widget in [self.slit_width_input, self.slit_length_input]:
            if not input_widget.isVisible():
                continue
            if input_widget.text() == "":
                input_widget.setStyleSheet(red)
                success = False
            else:
                try:
                    num = u.Quantity(input_widget.text()).value
                    if num <= 0:
                        input_widget.setStyleSheet(red)
                        success = False
                    else:
                        input_widget.setStyleSheet("")
                except ValueError:
                    input_widget.setStyleSheet(red)
                    success = False
        return success

    def apply(self):
        """Validate and replace current slit"""
        key = self.slit_type_combo.currentData()

        if not self.input_validation() and key != "default":
            return

        if key == "default":
            slit_info = self.mosviz_viewer.get_slit_dimensions_from_file()
            if slit_info is None:
                self.mosviz_viewer.slit_controller.clear_slits()
            else:
                self.mosviz_viewer.add_slit()
        else:
            width = (self.width * self.width_units).to(u.arcsec)
            length = (self.length * self.length_units).to(u.arcsec)
            self.mosviz_viewer.slit_controller.clear_slits()
            self.mosviz_viewer.add_slit(width=width, length=length)

        if self.mosviz_viewer.slit_controller.has_slits:
            self.mosviz_viewer.image_widget.draw_slit()
            self.mosviz_viewer.image_widget.set_slit_limits()
            self.mosviz_viewer.image_widget._redraw()

        self.cancel()

    def cancel(self):
        self.close()
