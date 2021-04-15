import sys
import os
from glob import glob
import re

from qtpy import compat
from qtpy.uic import loadUi
from qtpy.QtWidgets import QMainWindow, QApplication, QMessageBox
from qtpy.QtCore import Qt

from glue.config import menubar_plugin
from glue.utils.qt import pick_item
from glue.viewers.image.qt import StandaloneImageViewer
from glue.core.data_factories import load_data

from astropy.table import QTable
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS\

# this will be eventually imported from astropy.nddata.utils
from .cutout_lib import cutouts_from_fits
from ..table_generator import nirspec_table_generator

__all__ = ["go_make_cutouts", "natural_sort",
           "unique_id", "CutoutTool",
           "NIRSpecCutoutTool", "nIRSpec_cutout_tool",
           "GeneralCutoutTool", "general_cutout_tool"]


def go_make_cutouts(table, imagename, image_label, output_file_format=None,
                    output_dir_format=None, apply_rotation=False,
                    image_ext=0, clobber=False, verbose=True,
                    ispreview=False, report=None):
    """
    This function is a modified copy of astroimtools.cutout_tools.make_cutouts.
    Make cutouts from a 2D image and write them to FITS files.

    Catalog must have the following columns with unit info, where applicable:
        * ``'id'`` - ID string; no unit necessary.
        * ``'ra'`` - RA (e.g., in degrees).
        * ``'dec'`` - DEC (e.g., in degrees).
        * ``'cutout_x_size'`` - Cutout width (e.g., in arcsec).
        * ``'cutout_y_size'`` - Cutout height (e.g., in arcsec).
        * ``'cutout_pa'`` - Cutout angle (e.g., in degrees). This is only
          use if user chooses to rotate the cutouts. Positive value
          will result in a clockwise rotation.
        * ``'spatial_pixel_scale'`` - Pixel scale (e.g., in arcsec/pix).

    The following are no longer used, so they are now optional:
        * ``'slit_pa'`` - Slit angle (e.g., in degrees).
        * ``'slit_width'`` - Slit width (e.g., in arcsec).
        * ``'slit_length'`` - Slit length (e.g., in arcsec).

    Cutouts are organized as follows::
        working_dir/
            &lt;image_label&gt;_cutouts/
                &lt;id&gt;_&lt;image_label&gt;_cutout.fits

    Each cutout image is a simple single-extension FITS with updated WCS.
    Its header has the following special keywords:
        * ``OBJ_RA`` - RA of the cutout object in degrees.
        * ``OBJ_DEC`` - DEC of the cutout object in degrees.
        * ``OBJ_ROT`` - Rotation of cutout object in degrees.
    Can add Qt.WindowStaysOnTopHint to supper to keep window ontop.

    Parameters
    ----------
    table : QTable
        Catalog table defining the sources to cut out.
    imagename : str
        Image to cut.
    image_label : str
        Label to name the cutout sub-directory and filenames.
    output_file_format : str, optional
        Typically '{0}.fits'
    output_dir_format : str, optional
        Typically '{0}_cutouts'
    apply_rotation : bool, optional
        Cutout will be rotated to a given angle. Default is `False`.
    image_ext : int, optional
        Image extension to extract header and data. Default is 0.
    clobber : bool, optional
        Overwrite existing files. Default is `False`.
    verbose : bool, optional
        Print extra info. Default is `True`.
    report : _Report, optional
        Class that allows monitoring of the internal algorithm by the
        caller. Set to None if no reporting is needed.
    """
    if report:
        report.initialize(len(table))

    # Define output names.
    if not output_file_format:
        output_file_format = '{0}.fits'
    if not output_dir_format:
        output_dir_format = '{0}_cutouts'

    # Sub-directory, relative to working directory.
    path = output_dir_format.format(image_label)
    if not os.path.exists(path):
        os.mkdir(path)

    fits_cutouts = []
    for counter, row in enumerate(table):
        t = QTable(row)
        cutout = cutouts_from_fits(imagename, t, output_dir=path,
                                     overwrite=True, verbose=True)

        if cutout:
            fits_cutouts.append(cutout[0])
        if report:
            report.report(counter)

    if report:
        report.report(len(table)
                      )

    success_list = [True if type(e)==fits.hdu.image.PrimaryHDU else False
                    for e in fits_cutouts]
    success_counter = success_list.count(True)

    return fits_cutouts, success_counter, success_list


def natural_sort(array):
    """
    Function for natural sort (human sort)

    Parameters
    ----------
    array : list
        list of strings to be sorted.

    returns
    -------
    sorted_array: list
        A sorted list.
    """

    def isInt(char):
        if char.isdigit():
            return int(char)
        else:
            return char.lower()

    def key_gen(line):
        return [isInt(char) for char in re.split('(\d+)', line)]

    return sorted(array, key=key_gen)


def unique_id(ID, IDList):
    """
    Assigns a unique ID to each spectral target.
    A spectral target may appear in multiple files so
    unique_id assigns IDs by appending _<New number> to
    the spectral target ID.

    Parameters
    ----------
    ID : String
        Spectral target ID.
    IDList : Dictionary
        Keys are original IDs and the values are the
        numbers that were last used for ID generation.

    returns
    -------
    ID : String
        Unique ID.
    IDList : Dictionary
        Updated IDList.
    """
    keys = IDList.keys()
    if ID not in keys:
        IDList[ID] = 0
        return ID, IDList

    IDList[ID] += 1
    ID = ID+"_%s" % (IDList[ID])

    return ID, IDList


class _Report():
    """
    Class that enables the go_make_cutouts and related functions in
    nddata.utils to report their status and progress to the mosviz cutout
    tools GUIs. These classes call function report(*args, **kwargs) which
    acts as interface to this class.

    Parameters
    ---------
    progress_bar : QProgressBar
        a progress bar
    status_bar : QStatusBar
        a status bar
    kill : bool, optional
        a flag that allows the GUI to kill the cutout algorithm
    """
    def __init__(self, progress_bar, status_bar, kill=False):
        self.progress_bar = progress_bar
        self.status_bar = status_bar
        self.kill = kill

    def initialize(self, maximum, message="Making cutouts"):
        """
        Initialize the report.

        Parameters
        ---------
        maximum : int
            The maximum value to set in a progress bar
        message : str
            Text to display in status bar
        """
        self.maximum = maximum
        self.message = message

        if self.progress_bar is not None:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(self.maximum)
            self.progress_bar.reset()

        QApplication.processEvents()

    def report(self, value, message=None):
        """
        Report in progress and status bars.

        Parameters
        ----------
        value : int
            Current value for progress bar
        message : str
            Text to display in status bar. If None, the text defined
            at initialization time is used.
        """
        print("INSIDE", self.progress_bar, self.status_bar, value, message)
        if self.status_bar is not None:
            msg = self.message
            if message != None:
                msg = message
            self.status_bar().showMessage(
                msg + ("(%s/%s)"%(value, self.maximum)))

        if self.progress_bar is not None:
            self.progress_bar.setValue(value)

        QApplication.processEvents()


class CutoutTool(QMainWindow):

    def __init__ (self, session, parent=None):
        if parent is None:
            parent = session.application
        super(CutoutTool, self).__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.session = session

        self.progress_bar = None
        self.status_bar = None
        self.kill = False
        self.output_dir_format = '{0}_cutouts' #format(image_label)
        self.output_file_format = '{0}_{1}_cutout.fits' #format(ID, image_label)

    def get_spatial_pixel_scale(self, imagename):
        """
        Get spatial pixel scale from image.
        Parameters
        ----------
        imagename : str
            Path to image

        returns
        -------
        int : spatial_pixel_scale in arcsec.
        """
        header = fits.getheader(imagename)
        w = WCS(header)
        psm = w.pixel_scale_matrix
        spatial_pixel_scale = psm.flatten().max() * u.deg
        return spatial_pixel_scale.to(u.arcsec).value

    def abort(self):
        self.kill = True

    def closeEvent(self, event):
        parent = super(CutoutTool, self).parent()
        if (parent is not None and
            parent is not self.session.application):
            parent.raise_()
        super(CutoutTool, self).closeEvent(event)


class NIRSpecCutoutTool(CutoutTool):

    def __init__ (self, session, parent=None, spec_path=None, TableGen=None):
        super(NIRSpecCutoutTool, self).__init__(session, parent=parent)
        self.output_file_format = '{0}.fits'
        self.output_dir_format = 'mosviz_cutouts'

        if TableGen is None:
            self.tableGen = False
            self.TableGen = None
        else:
            self.tableGen = True
            self.TableGen = TableGen

        self.title = "NIRSpec Cutout Tool"

        if spec_path is None:
            self.spec_path = ""
        else:
            self.spec_path = spec_path
        self.TableGen = TableGen #instance
        self.img_path = ""
        self.save_path  = ""
        self.cutout_x_size = 0
        self.cutout_y_size = 0
        self.cutout_x_size_default = ""
        self.cutout_y_size_default = ""
        self.custom_save_path  = False
        self.imageExt = ['*.fits', '*.FITS', '*.fit', '*.FIT',
         '*.fts', '*.FTS', '*.fits.Z', '*.fits.z', '*.fitz',
         '*.FITZ', '*.ftz', '*.FTZ', '*.fz', '*.FZ']
        self.initUI()

        self.report = _Report(self.progress_bar, self.status_bar, self.kill)

    def initUI(self):

        plugin_path = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(plugin_path, "ui")
        ui_path = os.path.join(ui_dir, 'cutout_tool.ui')
        loadUi(ui_path, self)
        self.statusBar().showMessage("Waiting for user input")

        self.progress_bar = self.progressBar
        self.status_bar = self.statusBar
        self.progressBar.reset()
        self.save_path_display.setDisabled(True)

        if self.tableGen:
            self.spectra_user_input.setText(self.spec_path)
            self.spectra_user_input.setDisabled(True)
            self.spectra_browse_button.setDisabled(True)
            self.update_save()
        else:
            self.spectra_user_input.setText(self.spec_path)
            self.spectra_user_input.textChanged.connect(self.update_save)
            self.spectra_browse_button.clicked.connect(self.get_spec_path)

        self.start_button.clicked.connect(self.call_main)
        self.change_save_button.clicked.connect(self.custom_path)
        self.image_browse_button.clicked.connect(self.get_img_path)
        self.preview_button.clicked.connect(self.call_peview)

        self.x_user_input.setText(self.cutout_x_size_default)
        self.y_user_input.setText(self.cutout_y_size_default)
        self.x_user_input.selectAll()
        self.y_user_input.selectAll()

        self.show()

    def update_save(self):
        if not self.custom_save_path:
            self.save_path  = self.spectra_user_input.text()
            if self.save_path  == "":
                self.save_path_display.setText("")
            else:
                directory = self.output_dir_format.format("<programName>")
                self.save_path_display.setText(
                    os.path.join("<Spectra Directory>",
                        directory, "<ObjectID>.fits")
                    )

    def get_spec_path(self):
        """Browse spectra directory"""
        browse_input = compat.getexistingdirectory()
        self.raise_()
        if browse_input == "":
            return
        self.spec_path = browse_input
        self.spectra_user_input.setText(self.spec_path)
        self.spectra_user_input.setStyleSheet("")
        self.update_save()

    def get_img_path(self):
        """Browse to add image"""
        browse_input = compat.getopenfilename(filters=" ".join(self.imageExt))[0]
        self.raise_()
        if browse_input == "":
            return
        self.img_path = browse_input
        self.image_user_input.setText(self.img_path)
        self.image_user_input.setStyleSheet("")

    def custom_path(self):
        """
        User specified save path. Renders paths in output absolute
        when using MOSViz TableGen. Can also revert to default.
        """
        if self.change_save_button.text() == "Change" and self.tableGen:
            info = QMessageBox.information(self, "Info", "Changing the save destination will generate a MOSViz Table"
                                                 " that is unique to your computer (you will not be able to share it).")
        if not self.custom_save_path:
            self.save_path  = compat.getexistingdirectory()
            self.raise_()
            if self.save_path  == "":
                return
            directory = self.output_dir_format.format("<programName>")
            self.save_path_display.setText(
                    os.path.join(self.save_path,
                        directory, "<ObjectName>.fits")
                    )
            self.change_save_button.setText("Revert")
            self.custom_save_path = True
        else:
            self.custom_save_path  = False
            self.change_save_button.setText("Change")
            self.update_save()

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

        #Inputs to setStyleSheet
        failed = "background-color: rgba(255, 0, 0, 128);"
        works = ""

        self.spec_path = self.spectra_user_input.text()
        self.img_path = self.image_user_input.text()

        if not self.custom_save_path: #Just in case
            self.save_path  = self.spec_path

        try:
            self.cutout_x_size = float(self.x_user_input.text())
        except ValueError:
            self.cutout_x_size = -1
        if self.cutout_x_size > 0:
            self.x_user_input.setStyleSheet(works)
        else:
            self.x_user_input.setStyleSheet(failed)
            success = False

        try:
            self.cutout_y_size = float(self.y_user_input.text())
        except ValueError:
            self.cutout_y_size = -1
        if self.cutout_y_size > 0:
            self.y_user_input.setStyleSheet(works)
        else:
            self.y_user_input.setStyleSheet(failed)
            success = False

        if self.spec_path == "":
            self.spectra_user_input.setStyleSheet(failed)
            success = False
        else:
            self.spectra_user_input.setStyleSheet(works)

        if self.img_path == "":
            self.image_user_input.setStyleSheet(failed)
            success = False
        else:
            self.image_user_input.setStyleSheet(works)

        #Check if success to reduce pop-ups:
        if success:
            if not os.path.isdir(self.spec_path):
                info = QMessageBox.information(self, "Status:",
                                               "Broken path:\n\n"+self.spec_path)
                self.spectra_user_input.setStyleSheet(failed)
                success = False

            if not os.path.isfile(self.img_path):
                info = QMessageBox.information(self, "Status:",
                                               "Broken path:\n\n"+self.img_path)
                self.image_user_input.setStyleSheet(failed)
                success = False

        return success

    def make_catalog_table(self):
        catalog = nirspec_table_generator(self.spec_path)
        t = catalog.to_table()

        if t is None:
            return

        t.add_column(
            t.Column(
                data=[self.cutout_x_size for row in t]*u.arcsec,
                name="cutout_width"
            )
        )

        t.add_column(
            t.Column(
                data=[self.cutout_x_size for row in t]*u.arcsec,
                name="cutout_height"
            )
        )

        return t

    def write_skipped(self, table, success_table):
        path = os.path.join(
            self.save_path,
            "skipped_cutout_files.txt")
        with open(path, "w") as f:
            for i, x in enumerate(table['id']):
                status = success_table[i]
                if status == False:
                    f.write(x+"\n")

    def call_main(self):
        """
        Calls the main function and handles exceptions.
        """
        cwd = os.getcwd()
        try:
            self.main()
            os.chdir(cwd)
            self.start_button.setEnabled(True)
            self.start_button.setText("Start")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.call_main)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            self.close()
            os.chdir(cwd)
            raise

    def main(self):
        """
        Main function that uses information provided
        by the user and in the headers of spectra files
        to construct a catalog and make cutouts.
        """
        success = self.verify_input()
        if not success:
            self.statusBar().showMessage("Please fill in all fields")
            return

        # self.start_button.setText("Abort")
        # self.start_button.clicked.disconnect()
        # self.start_button.clicked.connect(self.abort)

        # temporary fix for non-existing abort functionality.
        self.start_button.setText("Working...")
        self.start_button.setEnabled(False)

        self.statusBar().showMessage("Making a list of files")
        QApplication.processEvents()

        t = self.make_catalog_table()

        if t is None:
            raise Exception("Spectra files were not found.")

        # Make cutouts using info in catalog.
        self.statusBar().showMessage("Making cutouts")

        output_path = os.path.join(self.save_path, self.output_dir_format)

        fits_cutouts, success_counter, success_table = go_make_cutouts(
            t, self.img_path, "cutouts",
            output_file_format=self.output_file_format,
            output_dir_format=output_path,
            clobber=True,
            apply_rotation=True,
            report=self.report)

        self.statusBar().showMessage("DONE!")

        # Give notice to user on status.
        string = "Cutouts were made for %s out of %s files\n\nSaved at: %s" %(
            success_counter, len(t), output_path)

        # save a list of failed cutouts
        if success_counter != len(t):
            self.write_skipped(t, success_table)
            string += "\n\nA list of spectra files "
            string += "without cutouts is saved in "
            string += "'skipped_cutout_files.txt' "
            string += "\n\nSaved at: %s" %os.path.join(
                self.save_path,
                "skipped_cutout_files.txt")

        info = QMessageBox.information(self, "Status:", string)

        if success_counter == 0:
            usr_ans = QMessageBox.question(self, '',
                                           "Would you like to load all generated cutouts into glue?",
                                           QMessageBox.Yes | QMessageBox.No)

            if usr_ans == QMessageBox.Yes:
                data = []
                for i, flag in enumerate(success_table):
                    if flag:
                        path = output_path
                        this_id = t["id"][i]
                        fname = os.path.join(
                            path, self.output_file_format.format(this_id))
                        data.append(load_data(fname))
                self.session.data_collection.merge(*data, label=self.output_dir_format)

        if self.tableGen and self.TableGen is not None:
            self.TableGen.cutout_response(output_path, self.custom_save_path)

        self.close()
        return

    def call_peview(self):
        """
        Calls the peview function and handles exceptions.
        """
        cwd = os.getcwd()
        try:
            self.preview()
            os.chdir(cwd)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            os.chdir(cwd)

    def preview(self):
        success = self.verify_input()
        if not success:
            self.statusBar().showMessage("Please fill in all fields")
            return

        t = self.make_catalog_table()

        if t is None:
            raise Exception("Spectra files were not found.")

        fb = list(t['id'])
        if len(fb) == 0:
            return

        row = pick_item(t, fb, title='Preview', label='Pick a target:')

        if row is None:
            return

        # Make cutouts using info in catalog.
        self.statusBar().showMessage("Making cutouts")

        output_path = os.path.join(self.save_path, self.output_dir_format)

        fits_cutouts, success_counter, success_table = go_make_cutouts(
            QTable(row), self.img_path, "cutouts",
            output_file_format=self.output_file_format,
            output_dir_format=output_path,
            clobber=True,
            apply_rotation=True,
            report=self.report)

        hdu = fits_cutouts[0]

        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.reset()
        QApplication.processEvents()

        if hdu is None:
            raise Exception("Could not make cutout. Object "
                            "may be out of the image's range.")

        if self.session is not None:
            iv = StandaloneImageViewer(hdu.data, parent=self.session.application)
            iv.setWindowFlags(iv.windowFlags() | Qt.Tool)
            iv.show()
        else:
            import matplotlib.pyplot as plt
            plt.imshow(hdu.data)
            plt.show()


class GeneralCutoutTool(CutoutTool):

    def __init__ (self, session, parent=None):
        super(GeneralCutoutTool, self).__init__(session, parent=parent)
        self.output_file_format = '{0}.fits'

        self.title = "General Cutout Tool"

        self.target_file_path = ""
        self.img_path = ""
        self.save_path  = ""
        self.cutout_x_size = 0
        self.cutout_y_size = 0
        self.cutout_x_size_default = ""
        self.cutout_y_size_default = ""
        self.custom_save_path  = False
        self.imageExt = ['*.fits', '*.FITS', '*.fit', '*.FIT',
         '*.fts', '*.FTS', '*.fits.Z', '*.fits.z', '*.fitz',
         '*.FITZ', '*.ftz', '*.FTZ', '*.fz', '*.FZ']
        self.initUI()

        self.report = _Report(self.progress_bar, self.status_bar,
                                 self.kill)

    def initUI(self):

        plugin_path = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(plugin_path, "ui")
        ui_path = os.path.join(ui_dir, 'general_cutout_tool.ui')
        loadUi(ui_path, self)
        self.statusBar().showMessage("Waiting for user input")

        self.progress_bar = self.progressBar
        self.status_bar = self.statusBar
        self.progressBar.reset()
        self.save_path_display.setDisabled(True)

        self.start_button.clicked.connect(self.call_main)
        self.target_browse_button.clicked.connect(self.get_target_path)
        self.change_save_button.clicked.connect(self.custom_path)
        self.image_browse_button.clicked.connect(self.get_img_path)
        self.target_user_input.textChanged.connect(self.update_save)
        self.preview_button.clicked.connect(self.call_peview)

        self.x_user_input.setText(self.cutout_x_size_default)
        self.y_user_input.setText(self.cutout_y_size_default)
        self.x_user_input.selectAll()
        self.y_user_input.selectAll()

        self.show()

    def update_save(self):
        if not self.custom_save_path:
            self.save_path = self.target_user_input.text()
            if self.save_path  == "":
                self.save_path_display.setText("")
            else:
                directory = self.output_dir_format.format("<ImgName>")
                self.save_path_display.setText(
                    os.path.join("<Target Catalog Directory>",
                        directory, "<ObjectName>.fits")
                    )

    def get_target_path(self):
        browse_input = compat.getopenfilename(filters="*.txt")[0]
        self.raise_()
        if browse_input == "":
            return
        self.target_file_path = browse_input
        self.target_user_input.setText(self.target_file_path)
        self.target_user_input.setStyleSheet("")
        self.update_save()

    def get_img_path(self):
        browse_input = compat.getopenfilename(filters=" ".join(self.imageExt))[0]
        self.raise_()
        if browse_input == "":
            return
        self.img_path = browse_input
        self.image_user_input.setText(self.img_path)
        self.image_user_input.setStyleSheet("")

    def custom_path(self):
        """
        User specified save path. Renders paths in output absolute.
        Can also revert to default.
        """
        if not self.custom_save_path:
            browse_input = compat.getexistingdirectory()
            self.raise_()
            if browse_input == "":
                return
            self.save_path = browse_input
            directory = self.output_dir_format.format("<programName>")
            self.save_path_display.setText(
                os.path.join(self.save_path,
                    directory, "<ObjectName>.fits")
                )
            self.change_save_button.setText("Revert")
            self.custom_save_path = True
        else:
            self.custom_save_path  = False
            self.change_save_button.setText("Change")
            self.update_save()

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

        #Inputs to setStyleSheet
        failed = "background-color: rgba(255, 0, 0, 128);"
        works = ""

        self.target_file_path = self.target_user_input.text()
        self.img_path = self.image_user_input.text()

        if not self.custom_save_path: #Just in case
            save_path  = self.target_user_input.text()
            self.save_path = os.path.dirname(save_path)

        try:
            self.cutout_x_size = float(self.x_user_input.text())
        except ValueError:
            self.cutout_x_size = -1
        if self.cutout_x_size > 0:
            self.x_user_input.setStyleSheet(works)
        else:
            self.x_user_input.setStyleSheet(failed)
            success = False

        try:
            self.cutout_y_size = float(self.y_user_input.text())
        except ValueError:
            self.cutout_y_size = -1
        if self.cutout_y_size > 0:
            self.y_user_input.setStyleSheet(works)
        else:
            self.y_user_input.setStyleSheet(failed)
            success = False

        if self.target_file_path == "":
            self.target_user_input.setStyleSheet(failed)
            success = False
        else:
            self.target_user_input.setStyleSheet(works)

        if self.img_path == "":
            self.image_user_input.setStyleSheet(failed)
            success = False
        else:
            self.image_user_input.setStyleSheet(works)

        #Check if success to reduce pop-ups:
        if success:
            if not os.path.isfile(self.target_file_path):
                info = QMessageBox.information(self, "Status:",
                    "Broken path:\n\n"+self.target_file_path)
                self.target_user_input.setStyleSheet(failed)
                success = False
            if not os.path.isfile(self.img_path):
                info = QMessageBox.information(self, "Status:",
                                               "Broken path:\n\n"+self.img_path)
                self.image_user_input.setStyleSheet(failed)
                success = False
        return success

    def make_catalog_table(self):
        spatial_pixel_scale = self.get_spatial_pixel_scale(self.img_path)

        catalog = []
        with open(self.target_file_path) as f:
            for line in f:
                if '#' in line:
                    continue
                line = line.replace("\n", "")
                row = line.split(" ")
                if len(row) != 3 and len(row) != 4:
                    raise Exception("Incorrect target catalog file format.")
                for i, r in enumerate(row[1:]):
                    i += 1
                    row[i] = float(r)
                row.append(spatial_pixel_scale)
                row.append(self.cutout_x_size) #cutout_x_size
                row.append(self.cutout_y_size) #cutout_y_size
                catalog.append(row)

        if len(catalog[0]) == 7:
            colNames = ["id", "ra", "dec", "slit_pa",
                "spatial_pixel_scale", "cutout_width", "cutout_height",]
        elif len(catalog[0]) == 6:
            colNames = ["id", "ra", "dec", "spatial_pixel_scale",
                "cutout_width", "cutout_height", ]
        else:
            raise Exception("Catalog generation unsuccessful.")

        t = QTable(rows=catalog, names=colNames)
        t["ra"].unit = u.deg
        t["dec"].unit = u.deg
        t["spatial_pixel_scale"].unit = (u.arcsec/u.pix)
        t["cutout_width"].unit = u.arcsec
        t["cutout_height"].unit = u.arcsec

        if len(row[0]) == 7:
            t["slit_pa"].unit = u.deg

        return t

    def write_skipped(self, table, success_table):
        path = os.path.join(
            self.save_path,
            "skipped_cutout_files.txt")
        with open(path, "w") as f:
            for i, x in enumerate(table['id']):
                status = success_table[i]
                if status == False:
                    f.write(x+"\n")

    def call_main(self):
        """
        Calls the main function and handles exceptions.
        """
        cwd = os.getcwd()
        try:
            self.main()
            os.chdir(cwd)
            self.start_button.setEnabled(True)
            self.start_button.setText("Start")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.call_main)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            self.close()
            os.chdir(cwd)
            raise

    def main(self):
        """
        Construct a catalog and make cutouts.
        """

        success = self.verify_input()
        if not success:
            self.statusBar().showMessage("Please fill in all fields")
            return

        # self.start_button.setText("Abort")
        # self.start_button.clicked.disconnect()
        # self.start_button.clicked.connect(self.abort)

        # temporary fix for non-existing abort functionality.
        self.start_button.setText("Working...")
        self.start_button.setEnabled(False)

        self.statusBar().showMessage("Making a list of files")
        QApplication.processEvents()

        t = self.make_catalog_table()

        #Change working path to save path
        cwd = os.getcwd()
        os.chdir(self.save_path)
        self.statusBar().showMessage("Making catalog")

        programName, file_extension = os.path.splitext(self.img_path)
        programName = os.path.basename(programName)

        #Make cutouts using info in catalog.
        self.statusBar().showMessage("Making cutouts")
        fits_cutouts, success_counter, success_table = go_make_cutouts(
            t, self.img_path, programName,
            output_file_format=self.output_file_format,
            output_dir_format=self.output_dir_format, clobber=True,
            apply_rotation=True, report=self.report)

        if self.kill:
            self.kill = False
            self.progress_bar.reset()
            self.statusBar().showMessage("Waiting for user input")
            return

        self.statusBar().showMessage("DONE!")
        directory = self.output_dir_format.format(programName)
        output_path = os.path.abspath(
            os.path.join(self.save_path, directory))

        #Give notice to user on status.
        string = "Cutouts were made for %s out of %s files\n\nSaved at: %s" %(
            success_counter, len(t), output_path)

        #If some spectra files do not have a cutout, a list of their names will be saved to
        # 'skipped_cutout_files.txt' in the save dir as the MOSViz Table file.
        if success_counter != len(t):
            self.write_skipped(t, success_table)
            string += "\n\nA list of spectra files"
            string += "without cutouts is saved in"
            string += "'skipped_cutout_files.txt'"
            string += "\n\nSaved at: %s" % os.path.join(
                self.save_path,
                "skipped_cutout_files.txt")

        info = QMessageBox.information(self, "Status:", string)

        #Change back dir.
        os.chdir(cwd)

        usr_ans = QMessageBox.question(self, '',
            "Would you like to load all generated cutouts into glue?",
            QMessageBox.Yes | QMessageBox.No)

        if usr_ans == QMessageBox.Yes:
            os.chdir(self.save_path)
            data = []
            for i, flag in enumerate(success_table):
                if flag:
                    path = self.output_dir_format.format(programName)
                    this_id = t["id"][i]
                    fname = os.path.join(
                        path, self.output_file_format.format(this_id, programName))
                    data.append(load_data(fname))
            self.session.data_collection.merge(*data, label="%s_Cutouts" %programName)
            os.chdir(cwd)

        self.close()
        return

    def call_peview(self):
        """
        Calls the peview function and handles exceptions.
        """
        cwd = os.getcwd()
        try:
            self.preview()
            os.chdir(cwd)
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            os.chdir(cwd)

    def preview(self):
        success = self.verify_input()
        if not success:
            self.statusBar().showMessage("Please fill in all fields")
            return

        t = self.make_catalog_table()

        index = pick_item(range(len(t)) , t["id"].tolist(),
            title='Preview', label='Pick a target:')

        if index is None:
            return

        t = QTable(t[index])

        programName, file_extension = os.path.splitext(self.img_path)
        programName = os.path.basename(programName)

        #Make cutouts using info in catalog.
        self.statusBar().showMessage("Making cutouts")
        fits_cutouts, success_counter, success_table = go_make_cutouts(
            t, self.img_path, programName,
            output_file_format=self.output_file_format,
            output_dir_format=self.output_dir_format, clobber=True,
            apply_rotation=True, ispreview=True, report=self.report)
        hdu = fits_cutouts[0]

        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.reset()
        QApplication.processEvents()

        if hdu is None:
            raise Exception("Could not make cutout. "
                "Object may be out of the image's range.")

        if self.session is not None:
            iv = StandaloneImageViewer(hdu.data)
            iv.setWindowFlags(iv.windowFlags() | Qt.Tool)
            iv.show()
        else:
            import matplotlib.pyplot as plt
            plt.imshow(hdu.data)
            plt.show()


@menubar_plugin("Cutout Tool (JWST/NIRSpec MSA)")
def nIRSpec_cutout_tool(session, data_collection):
    ex = NIRSpecCutoutTool(session)
    return

@menubar_plugin("General Purpose Cutout Tool")
def general_cutout_tool(session, data_collection):
    ex = GeneralCutoutTool(session)
    return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex1 = NIRSpecCutoutTool()
    ex2 = GeneralCutoutTool()
    sys.exit(app.exec_())
