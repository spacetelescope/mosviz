from ..third_party.qtpy.QtCore import QThread, pyqtSignal
import os
import logging

from ..core.data import MOSData
from ..interfaces.registries import loader_registry


class FileLoadThread(QThread):
    status = pyqtSignal(str, int)
    result = pyqtSignal(MOSData)

    def __init__(self, parent=None):
        super(FileLoadThread, self).__init__(parent)
        self.file_name = ""
        self.file_filter = ""

    def __call__(self, file_name, file_filter):
        self.file_name = file_name
        self.file_filter = file_filter

    def run(self):
        self.status.emit("Loading file...", 0)
        data = self.read_file(self.file_name, self.file_filter)

        if data is not None:
            self.status.emit("File loaded successfully!", 5000)
        else:
            self.status.emit("An error occurred while loading file.", 5000)

        if data is not None:
            self.result.emit(data)
        else:
            logging.error("Could not open file.")

    def read_file(self, file_name, file_filter):
        """
        Convenience method that directly reads a spectrum from a file.
        This exists mostly to facilitate development workflow. In time it
        could be augmented to support fancier features such as wildcards,
        file lists, mixed file types, and the like.
        Note that the filter string is hard coded here; its details might
        depend on the intrincacies of the registries, loaders, and data
        classes. In other words, this is brittle code.
        """
        file_name = str(file_name)
        file_ext = os.path.splitext(file_name)[-1]

        try:
            data = MOSData.read(file_name, format=file_filter)
            return data
        except:
            logging.error("Incompatible loader for selected data: {"
                          "}".format(file_filter))
