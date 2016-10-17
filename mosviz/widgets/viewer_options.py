import os

from qtpy.QtWidgets import QWidget

from glue.utils.qt.widget_properties import CurrentComboDataProperty

__all__ = ["OptionsWidget"]


class OptionsWidget(QWidget):
    def __init__(self, parent=None, data_viewer=None):
        super(OptionsWidget, self).__init__(parent=parent)
