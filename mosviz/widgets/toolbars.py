import os

from glue.viewers.common.qt.toolbar import BasicToolbar
from glue.viewers.common.qt.tool import CheckableTool, Tool

from qtpy.QtWidgets import QAction, QComboBox, QSpacerItem
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt


class CyclePreviousTool(Tool):
    def __init__(self, viewer, toolbar=None):
        super(CyclePreviousTool, self).__init__(viewer=viewer)
        self.tool_id = 'mv:previous'
        self.action_text = "Previous"
        self.tool_tip = "Previous source in selection"
        self.shortcut = "P"
        self.checkable = False
        self.toolbar = toolbar

    def activate(self):
        pass


class CycleForwardTool(Tool):
    def __init__(self, viewer, toolbar=None):
        super(CycleForwardTool, self).__init__(viewer=viewer)
        self.tool_id = 'mv:next'
        self.action_text = "Next"
        self.tool_tip = "Next source in selection"
        self.shortcut = "N"
        self.checkable = False
        self.toolbar = toolbar

    def activate(self):
        pass


class MOSViewerToolbar(BasicToolbar):
    def __init__(self, *args, **kwargs):
        super(MOSViewerToolbar, self).__init__(*args, **kwargs)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Define icon path
        icon_path = os.path.join(os.path.dirname(__file__),
                                 'ui', 'icons')

        # Define the toolbar actions
        self.cycle_previous_action = QAction(
            QIcon(os.path.join(icon_path, "Previous-96.png")),
            "Previous", self)
        self.cycle_next_action = QAction(
            QIcon(os.path.join(icon_path, "Next-96.png")),
            "Next", self)

        # Include the dropdown widget
        self.source_select = QComboBox()

        # Add the items to the toolbar
        self.addAction(self.cycle_previous_action)
        self.addAction(self.cycle_next_action)
        self.addWidget(self.source_select)
        self.addSeparator()

        # Include a button to open spectrum in specviz
        self.open_specviz = QAction(
            QIcon(os.path.join(icon_path, "External-96.png")),
            "Open in SpecViz", self)
        self.addAction(self.open_specviz)


    def _setup_connections(self):
        pass