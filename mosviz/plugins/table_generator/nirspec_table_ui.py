import sys
import os
from glob import glob

from qtpy import compat
from qtpy.uic import loadUi
from qtpy.QtWidgets import QMainWindow, QApplication, QMessageBox
from qtpy.QtCore import Qt

from glue.config import menubar_plugin
from glue.core.data_factories import load_data

from astropy.table import QTable
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS

from ..cutout_tool import NIRSpecCutoutTool
from .nirspec_table import nirspec_table_generator
from ...viewers.mos_viewer import MOSVizViewer

__all__ = ["NIRSpecTableGen", "nIRSpec_table_gen"]


class NIRSpecTableGen(QMainWindow):

    def __init__ (self, parent=None):
        super(NIRSpecTableGen, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.parent = parent
        self.session = None
        if parent is not None and hasattr(parent, "session"):
            self.session = parent.session

        self.title = "MOSViz Table Generator for NIRSpec"
        self.spec_path = ""
        self.cutout_path = ""
        self.save_file_name = ""
        self.save_file_dir = ""
        self.custom_save_path = False
        self.abs_path = False
        self.CutoutTool = None
        self.image_ext = ['*.fits', '*.FITS', '*.fit', '*.FIT',
        '*.fts', '*.FTS', '*.fits.Z', '*.fits.z', '*.fitz',
        '*.FITZ', '*.ftz', '*.FTZ', '*.fz', '*.FZ']
        self.initUI()

    def initUI(self):
        """
        Set up user interface by loading the .ui file
        and configuring items in the GUI.
        """
        plugin_path = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(plugin_path, "ui")
        ui_path = os.path.join(ui_dir, 'table_generator.ui')
        loadUi(ui_path, self)

        self.setWindowTitle(self.title)
        self.statusBar().showMessage("Waiting for user input")

        #Set up no cutout option
        self.no_cutout_radio.setChecked(True)
        self._no_cutout_radio_toggled()

        #Set up radio buttons
        self.no_cutout_radio.toggled.connect(self._no_cutout_radio_toggled)
        self.add_cutout_radio.toggled.connect(self._add_cutout_radio_toggled)

        #Set up click buttons
        self.spectra_browse_button.clicked.connect(self.get_spec_path)
        self.add_cutout_button.clicked.connect(self.get_cutout_path)
        self.make_cutouts_button.clicked.connect(self.call_cutout)
        self.default_filename_button.clicked.connect(self.default_filename)
        self.generate_table_button.clicked.connect(self.call_main)
        self.change_save_path_button.clicked.connect(self.change_save_path)

        #Set up defaults
        self.default_filename()
        self.default_save_dir()

        self.show()

    def _no_cutout_radio_toggled(self):
        self.make_cutouts_button.setDisabled(True)
        self.add_cutout_button.setDisabled(True)
        self.cutout_path_display.setDisabled(True)
        self.cutout_dir_label.setDisabled(True)
        self.cutout_path_display.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")

    def _add_cutout_radio_toggled(self):
        self.make_cutouts_button.setDisabled(False)
        self.add_cutout_button.setDisabled(False)
        self.cutout_path_display.setDisabled(False)
        self.cutout_dir_label.setDisabled(False)
        self.cutout_path_display.setDisabled(False)
        self.cutout_path_display.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")

    def default_filename(self):
        self.save_file_name = "mosviz_table.ecsv"
        self.filename_user_input.setText(self.save_file_name)
        self.filename_user_input.setStyleSheet("")

    def default_save_dir(self):
        path = "<Directory Containing NIRSpec Spectra>"
        self.save_path_display.setText(path)

    def get_spec_path(self):
        """Browse spectra directory"""
        browse_input = compat.getexistingdirectory()
        self.raise_()
        if browse_input == "":
            return
        self.spec_path = browse_input
        self.spectra_user_input.setText(self.spec_path)
        self.spectra_user_input.setStyleSheet("")
        return

    def get_cutout_path(self):
        """Browse cutout directory"""
        browse_input = compat.getexistingdirectory()
        self.raise_()
        if browse_input == "":
            return

        self.cutout_path = browse_input
        self.cutout_path_display.setText(self.cutout_path)
        self.cutout_path_display.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")
        return

    def remove_cutout(self):
        """Remove cutout selection"""
        self.cutout_path = ""
        self.abs_path = False
        self.cutout_path_display.setText(self.cutout_path)
        self.cutout_path_display.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")
        return

    def change_save_path(self):
        """
        User specified save path. Renders paths in output absolute.
        Can also revert to default.
        """
        if self.change_save_path_button.text() == "Change":
            info = QMessageBox.information(self, "Info", "Changing the save destination will generate a MOSViz Table"
                                                 " that is unique to your computer (you will not be able to share it).")
        if self.custom_save_path  == False:
            browse_input = compat.getexistingdirectory()
            self.raise_()
            if browse_input == "":
                return
            self.save_file_dir  = browse_input
            self.save_path_display.setText(self.save_file_dir)
            self.change_save_path_button.setText("Revert")
            self.custom_save_path  = True
        else:
            self.custom_save_path  = False
            self.change_save_path_button.setText("Change")
            self.default_save_dir()

    def _write_skipped(self, skipped):
        """
        Save a list of skipped spectra files to file.
        """
        name = ".".join(self.save_file_name.split(".")[:-1])
        file_name = "skipped_files_%s.txt" %name
        with open(file_name, "w") as f:
            for items in skipped:
                line = " : ".join(items)+"\n"
                f.write(line)

        info = QMessageBox.information(self, "Info", "Some spectra files were not included in the generated MOSViz Table."
                                       " A list of the these files and the reason they were skipped has been saved to\n\n "
                                       " %s. " %file_name)


    def verify_input(self):
        """
        Process information in the input boxes.
        Checks if user inputs are functional.

        Returns
        -------
        success : bool
            True if no input errors, False otherwise.

        """
        self.statusBar().showMessage("Reading input")

        success = True
        self.spec_path = self.spectra_user_input.text()
        self.save_file_name = self.filename_user_input.text()

        if self.spec_path == "":
            self.spectra_user_input.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            success = False
        else:
            self.spectra_user_input.setStyleSheet("")

        if self.save_file_name == "" or "/" in self.save_file_name or "\\" in self.save_file_name:
            self.filename_user_input.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            success = False
        else:
            self.filename_user_input.setStyleSheet("")

        if self.add_cutout_radio.isChecked():
            self.cutout_path = self.cutout_path_display.text()
            if self.cutout_path == "":
                self.cutout_path_display.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                success = False
            else:
                self.cutout_path_display.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        if success:
            if not os.path.isdir(self.spec_path):
                info = QMessageBox.information(self, "Error", "Broken path:\n\n"+self.spec_path)
                self.spectra_user_input.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                success = False
            else:
                if not self.custom_save_path:
                    self.save_file_dir = self.spec_path

            if self.add_cutout_radio.isChecked():
                if not os.path.isdir(self.cutout_path):
                    info = QMessageBox.information(self, "Error", "Broken path:\n\n"+self.cutout_path)
                    self.cutout_path_display.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                    success = False

                if (not os.path.samefile(self.spec_path,
                    os.path.dirname(self.cutout_path)) and
                    not self.abs_path and not self.cutout_path):
                    usr_ans = QMessageBox.question(self, "Path Warning",
                        "The cutout directory is not in the spectra directory, "
                        "this will generate a MOSViz Table "
                        "that is unique to your computer "
                        "(you will not be able to share it). Continue?",
                        QMessageBox.Yes | QMessageBox.No)

                    if usr_ans == QMessageBox.Yes:
                        self.abs_path = True
                    else:
                        success = False
        return success

    def call_cutout(self):
        self.spec_path = self.spectra_user_input.text()
        if self.spec_path == "":
            self.spectra_user_input.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            info = QMessageBox.information(self, "Error", "Please provide directory containing NIRSpec spectra files.")
            return
        else:
            self.spectra_user_input.setStyleSheet("")
            if not os.path.isdir(self.spec_path):
                self.spectra_user_input.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                info = QMessageBox.information(self, "Error", "Broken path:\n\n"+self.spec_path)
                return
        if self.CutoutTool is not None:
            if self.CutoutTool.isVisible():
                info = QMessageBox.information(self, "Status",
                    "Error: Cutout tool is still running.")
                self.CutoutTool.raise_()
                return
            else:
                self.CutoutTool = None
        try:
            self.CutoutTool = NIRSpecCutoutTool(self.parent.session,
                parent=self, spec_path=self.spec_path, TableGen=self)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", "Cutout tool failed: "+str(e))

    def cutout_response(self, cutout_path, abs_path):
        self.cutout_path = cutout_path
        self.cutout_path_display.setText(self.cutout_path)
        self.cutout_path_display.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")
        self.abs_path = abs_path
        self.CutoutTool = None
        self.raise_()

    def call_main(self):
        """
        Calls the main function and handles exceptions.
        """
        if self.CutoutTool is not None:
            if self.CutoutTool.isVisible():
                info = QMessageBox.information(self, "Status",
                    "Error: Cutout tool is still running.")
                self.CutoutTool.raise_()
                return
            else:
                self.CutoutTool = None
        cwd = os.getcwd()
        try:
            self.main()
            os.chdir(cwd)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            self.close()
            os.chdir(cwd)
            raise

    def main(self):
        """
        Main metod that will take input from the user, make a
        MOSViz Table and save it to a file. It will use the information
        in the headers of the spectra files to fill in rows of the table.
        If the user has cutout, it will look for an image file with the
        corresponding object name and add it to the Table.
        """
        success = self.verify_input()
        if not success:
            self.statusBar().showMessage("Input error")
            return

        self.generate_table_button.setDisabled(True)
        self.statusBar().showMessage("Making Table")
        QApplication.processEvents()

        output_path = os.path.join(self.save_file_dir, self.save_file_name)

        source_catalog = nirspec_table_generator(self.spec_path,
                                                 cutout_path=self.cutout_path,
                                                 output_path=output_path)

        self.statusBar().showMessage("DONE!")

        info = QMessageBox.information(self, "Status", "Catalog saved at:\n"+output_path)

        if self.session is not None:
            usr_ans = QMessageBox.question(self, '',
                                           "Would you like to open {}?".format(self.save_file_name),
                                           QMessageBox.Yes | QMessageBox.No)

            if usr_ans == QMessageBox.Yes:
                self.hide()
                data = load_data(output_path)
                self.session.data_collection.append(data)
                self.session.application.new_data_viewer(MOSVizViewer, data=self.session.data_collection[-1])

        self.close()
        return


@menubar_plugin("MOSViz Table Generator (JWST/NIRSpec MSA)")
def nIRSpec_table_gen(session, data_collection):
    ex = NIRSpecTableGen(session.application)
    return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = NIRSpecTableGen()
    sys.exit(app.exec_())
