import sys
import os
from glob import glob

from qtpy import compat
from qtpy.uic import loadUi
from qtpy.QtWidgets import QMainWindow, QApplication, QMessageBox
from qtpy.QtCore import Qt

from glue.config import menubar_plugin

from astropy.table import QTable
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS

from .. import UI_DIR
from .cutout_tool import natural_sort, unique_id, NIRSpecCutoutTool

__all__ = ["NIRSpecTableGen", "nIRSpec_table_gen"]


class NIRSpecTableGen(QMainWindow):

    def __init__ (self, parent=None):
        super(NIRSpecTableGen, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.parent = parent

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
        path = os.path.join(UI_DIR, 'table_generator.ui')
        loadUi(path, self)

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
        self.remove_cutout_button.clicked.connect(self.remove_cutout)

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
        self.save_file_name = "MOSViz_Table.txt"
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

    def get_cutout(self, fn, ID):
        """
        Searches and attempts to match cutout with target names.
        It will check for images with the names containing the unique ID provided.
        If none are found it will search for images with original IDs in their names.
        If no images are found 'None' is returned as a place holder.

        Parameters
        ----------
        fn : String
            Spectra file name. (Used to get original ID)
        ID : String
            Unique ID.

        returns
        -------
        String
            A file name of cutout if image is found. "None" else.
        """
        img_fn = ID+".fits"
        img_fn = os.path.join(self.cutout_path, img_fn)

        if os.path.isfile(img_fn):
            if self.abs_path or self.custom_save_path:
                return os.path.abspath(img_fn)
            else:
                return os.path.relpath(img_fn, self.spec_path)

        name = os.path.basename(fn)
        name = name.split("_")

        img_fn = name[1]+".fits"
        img_fn = os.path.join(self.cutout_path, img_fn)

        if os.path.isfile(img_fn):
            if self.abs_path or self.custom_save_path:
                return os.path.abspath(img_fn)
            else:
                return os.path.relpath(img_fn, self.spec_path)
        else:
            return "None"

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
        except:
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
        self.statusBar().showMessage("Making a list of files")

        target_names = []
        fb = [] # File Base
        skipped = [] #List of files skipped.
        searchPath = os.path.join(self.spec_path, "*s2d.fits")
        for fn in glob(searchPath):
            name = os.path.basename(fn)
            name = name.split("_") #Split up file name
            if len(name) != 5:
                skipped.append([fn, "File name format not compliant."])
                continue
            name = name[-4] # Get the target name from file
            target_names.append(name)
            fb.append(fn)

        #If no files are found, return
        if len(fb) == 0:
            self.statusBar().showMessage("NIRSpec files not found")
            self.generate_table_button.setDisabled(False)
            info = QMessageBox.information(self, "Status", "No NIRSpec files found in this directory\n"
                "File Name Format:\n\n"
                "<programName>_<objectName>_<instrument_filter>_ <grating>_<s2d|x1d>.fits")
            return

        fb = natural_sort(fb)

        #Change working path to save path
        cwd = os.getcwd()
        os.chdir(self.save_file_dir)
        self.statusBar().showMessage("Making catalog")
        QApplication.processEvents()

        #Setup local catalog.
        catalog = []
        IDList = {} #Counter for objects with the same ID


        #Extract info from spectra files and save to catalog.
        projectName = os.path.basename(fb[0]).split("_")[0]
        for idx, fn in enumerate(fb): #For file name in file base:
            row = []

            #Catch file error or load WCS:
            filex1d = fn.replace("s2d.fits", "x1d.fits")
            if os.path.isfile(filex1d):
                try:
                    headx1d = fits.open(filex1d)['extract1d'].header
                    wcs = WCS(headx1d)
                    w1, w2 = wcs.wcs_pix2world(0., 0., 1)
                    w1 = w1.tolist()
                    w2 = w2.tolist()
                except Exception as e:
                    print("WCS Read Failed:", e, ":", filex1d)
                    skipped.append([filex1d, str(e)])
                    continue
            else:
                skipped.append([fn, "x1d counterpart not found."])
                continue

            try:
                head = fits.getheader(fn)
            except Exception as e:
                print("Header Read Failed:", e, ":", fn)
                skipped.append([fn, str(e)])
                continue

            #Make row for catalog:
            ID = target_names[idx]
            ID, IDList = unique_id(ID, IDList)

            if self.add_cutout_radio.isChecked():
                cutout = self.get_cutout(fn, ID)
            else:
                cutout = "None"

            if self.abs_path or self.custom_save_path:
                spectrum1d = os.path.abspath(fn.replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.abspath(fn)
            else:
                spectrum1d = os.path.join(".", os.path.basename(fn).replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.join(".", os.path.basename(fn))

            row.append(ID) #id
            row.append(w1) #ra
            row.append(w2) #dec
            row.append(spectrum1d) #spectrum1d
            row.append(spectrum2d) #spectrum2d
            row.append(cutout) #cutout
            row.append(0.2) #slit_width
            row.append(3.3) #slit_length
            row.append(head["CDELT2"]) #pix_scale (spatial_pixel_scale)
            row.append(head["PA_APER"]) #slit_pa

            catalog.append(row) #Add row to catalog

        #Write Skipped Files
        searchPath = os.path.join(self.spec_path, "*x1d.fits")
        for fn in glob(searchPath):
            name = os.path.basename(fn)
            name = name.split("_") #Split up file name
            if len(name) != 5:
                skipped.append([fn, "File name format not compliant."])
                continue
            files2d = fn.replace("x1d.fits", "s2d.fits")
            if not os.path.isfile(files2d):
                skipped.append([fn, "s2d counterpart not found"])

        if len(skipped) > 0:
            self._write_skipped(skipped)

        #if all spectra files were skipped
        if len(catalog) == 0:
            info = QMessageBox.critical(self, "Error", "MOSViz Table not generated: "
                                        "All spectra files were skipped.")
            os.chdir(cwd)
            self.close()
            return

        #Make and write MOSViz table
        self.statusBar().showMessage("Making MOSViz catalog")

        colNames = ["id", "ra", "dec", "spectrum1d", "spectrum2d", "cutout",
                    "slit_width", "slit_length", "spatial_pixel_scale", "slit_pa"]
        t = QTable(rows=catalog, names=colNames)
        t["ra"].unit = u.deg
        t["dec"].unit = u.deg
        t["slit_width"].unit = u.arcsec
        t["slit_length"].unit = u.arcsec
        t["spatial_pixel_scale"].unit = (u.arcsec/u.pix)
        t["slit_pa"].unit = u.deg

        self.statusBar().showMessage("Saving MOSViz catalog")
        #Write MOSViz Table to file.
        t.write(self.save_file_name, format="ascii.ecsv", overwrite=True)

        #Change back dir.
        self.statusBar().showMessage("DONE!")
        os.chdir(cwd)

        moscatalogname = os.path.abspath(os.path.join(self.save_file_dir, self.save_file_name))
        info = QMessageBox.information(self, "Status", "Catalog saved at:\n"+moscatalogname)

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
