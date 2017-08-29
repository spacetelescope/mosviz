from __future__ import absolute_import, division, print_function

import sys
import os
from glob import glob
from time import sleep
import numpy as np
import random as rn
from functools import partial

from qtpy import compat
from qtpy.uic import loadUi
from qtpy.QtWidgets import QMainWindow,QApplication
from qtpy.QtWidgets import QWidget,QMessageBox
from qtpy.QtCore import Qt

from glue.config import menubar_plugin

from astropy.table import QTable, Column
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS, NoConvergence
from astropy.coordinates import SkyCoord
from astropy.nddata.utils import (Cutout2D, NoOverlapError)
from astropy import log
from astropy.coordinates import Angle

from .. import UI_DIR

__all__ = ['TableGen','nIRSpec_table_gen']

class TableGen(QMainWindow):

    def __init__ (self, parent=None):
        super(TableGen,self).__init__(parent,Qt.WindowStaysOnTopHint)
        self.title = "MOSViz Table Generator for NIRSpec"
        self.spec_path = ""
        self.img_path = ""
        self.cutouts_option = False
        self.abs_path = False
        self.image_ext = ['*.fits', '*.FITS', '*.fit', '*.FIT',
         '*.fts', '*.FTS', '*.fits.Z', '*.fits.z', '*.fitz',
         '*.FITZ', '*.ftz', '*.FTZ', '*.fz', '*.FZ']
        self.initUI()

    def initUI(self):
        path = os.path.join(UI_DIR, 'table_generator.ui')
        loadUi(path, self)

        self.setWindowTitle(self.title)
        self.statusBar().showMessage("Waiting for user input")

        self.noCutoutsRadioButton.setChecked(True)

        self.imageBrowseButton.setDisabled(True)
        self.inImage.setDisabled(True)
        self.inImage.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        self.genTableButton.clicked.connect(self.main)
        self.noCutoutsRadioButton.toggled.connect(self.no_cutout)
        self.addCutoutsRadioButton.toggled.connect(self.add_cutout)
        self.specBrowseButton.clicked.connect(self.get_spec_path)
        self.imageBrowseButton.clicked.connect(self.get_img_path)

        self.show()

    def no_cutout(self):
        self.imageBrowseButton.setDisabled(True)
        self.inImage.setDisabled(True)
        self.inImage.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        return

    def add_cutout(self):
        self.imageBrowseButton.setDisabled(False)
        self.inImage.setDisabled(False)
        self.inImage.setStyleSheet("")
        return

    def get_spec_path(self):
        self.spec_path = compat.getexistingdirectory()
        self.inSpectra.setText(self.spec_path)
        return

    def get_img_path(self):
        self.img_path = compat.getexistingdirectory()
        self.inImage.setText(self.img_path)
        return

    def check_image_path(self):
        same_path = os.path.samefile(os.path.dirname(self.img_path),
                            os.path.abspath(self.spec_path))
        if not same_path:
            self.abs_path = True
        return

    def collect_text(self):
        """
        Process information in the input boxes.
        Checks if user inputs are functional.

        Return
        ------
        userOk : bool
            True for success, False otherwise.

        """
        self.statusBar().showMessage("Reading input")
        self.spec_path = self.inSpectra.text()
        self.img_path = self.inImage.text()

        userOk = True #meaning did the user input correctly?

        if self.spec_path == "":
            self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.inSpectra.setStyleSheet("")

        if self.addCutoutsRadioButton.isChecked():
            if self.img_path == "":
                self.inImage.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False
            else:
                self.inImage.setStyleSheet("")

        if userOk:
            if not os.path.isdir(self.spec_path):
                info = QMessageBox.information(self, "Status:", "Broken path:\n\n"+self.spec_path)
                self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False

            if self.addCutoutsRadioButton.isChecked():
                if not os.path.isdir(self.img_path):
                    info = QMessageBox.information(self, "Status:", "Broken path:\n\n"+self.img_path)
                    self.inImage.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                    userOk = False
                else:
                    self.check_image_path()
            return userOk

    def unique_id(self, ID, IDList):
        keys = IDList.keys()
        if ID not in keys:
            IDList[ID] = 0 
            return ID, IDList

        IDList[ID] += 1
        ID = ID+"-%s"%(IDList[ID])

        return ID, IDList

    def get_cutout(self, fn, ID):
        name = os.path.basename(fn)
        name = name.split("_")

        img_fn = "_".join([ID,name[0],"cutout.fits"])
        img_fn = os.path.join(self.img_path, img_fn)

        if os.path.isfile(img_fn):
            if self.abs_path:
                return os.path.abspath(img_fn)
            else:
                return os.path.relpath(img_fn, self.spec_path)

        img_fn = "_".join([name[1],name[0],"cutout.fits"])
        img_fn = os.path.join(self.img_path, img_fn)

        if os.path.isfile(img_fn):
            if self.abs_path:
                return os.path.abspath(img_fn)
            else:
                return os.path.relpath(img_fn, self.spec_path)
        else:
            return "None"


    def main(self):
        """
        Main metod that will take input from the user, make a 
        MOSViz Table and save it to a file. It will use the information
        in the headers of the spectra files to fill in rows of the table.
        If the user has cutouts, it will look for an image file with the corresponding
        object + project name and add it to the Table. 
        """
        userOK = self.collect_text() #meaning did the user input ok?
        if not userOK:
            self.statusBar().showMessage("Please fill in all fields")
            return

        self.genTableButton.setDisabled(True)
        self.statusBar().showMessage("Making a list of files")

        target_names = []
        fb = [] # File Base
        searchPath = os.path.join(self.spec_path,"*s2d.fits")
        for fn in glob(searchPath):
            name = os.path.basename(fn)
            name = name.split("_") #Split up file name
            if len(name) != 5:
                continue
            name = name[-4] # Get the target name from file
            target_names.append(name)
            fb.append(fn)

        #If no files are found, close the app
        if len(fb) == 0:
            self.statusBar().showMessage("NIRSpec files not found")
            self.genTableButton.setDisabled(False)
            info = QMessageBox.information(self, "Status:", "No NIRSpec files found in this directory\n"
                "File Name Format:\n\n"
                "<programName>_<objectName>_<instrument_filter>_ <grating>_<s2d|x1d>.fits")
            self.close()            
            return

        #Change working path to save path
        cwd = os.getcwd()
        os.chdir(self.spec_path)
        self.statusBar().showMessage("Making catalog")

        #Setup local catalog. 
        catalog = []
        IDList = {} #Counter for objects with the same ID 

        #Extract info from spectra files and save to catalog.
        projectName = os.path.basename(fn).split("_")[0]
        for idx, fn in enumerate(fb): #For file name in file base:
            row = []
            headx1d = fits.open(fn.replace("s2d.fits", "x1d.fits"))['extract1d'].header
            wcs = WCS(headx1d)
            w1, w2 = wcs.wcs_pix2world(0., 0., 1)
            w1 = w1.tolist()
            w2 = w2.tolist()

            head = fits.getheader(fn)
            ID = target_names[idx]
            ID, IDList = self.unique_id(ID, IDList)

            if self.addCutoutsRadioButton.isChecked():
                cutout = self.get_cutout(fn, ID)
            else:
                cutout = "None"

            if self.abs_path:
                spectrum1d = os.path.abspath(fn.replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.abspath(fn)
            else:
                spectrum1d = os.path.join(".",os.path.basename(fn).replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.join(".",os.path.basename(fn))

            row.append(ID) #id
            row.append(w1) #ra
            row.append(w2) #dec
            row.append(spectrum1d) #spectrum1d
            row.append(spectrum2d) #spectrum2d
            row.append(cutout) #cutout
            row.append(0.2) #slit_width
            row.append(3.3) #slit_length
            row.append(head["CDELT2"]) #pix_scale (spatial_pixel_scale)

            catalog.append(row) #Add row to catalog

        #Make and write MOSViz table 
        self.statusBar().showMessage("Making MOSViz catalog")

        colNames = ["id","ra","dec","spectrum1d","spectrum2d","cutout",
                    "slit_width","slit_length","pix_scale"]
        t = QTable(rows=catalog, names=colNames)
        t["ra"].unit = u.deg
        t["dec"].unit = u.deg
        t["slit_width"].unit = u.arcsec
        t["slit_length"].unit = u.arcsec
        t["pix_scale"].unit = (u.arcsec/u.pix)

        self.statusBar().showMessage("Saving MOSViz catalog")
        #Write MOSViz Table to file.
        moscatalogname = projectName+"_MOSViz_Table.txt"
        t.write(moscatalogname, format="ascii.ecsv", overwrite=True)
        
        #Change back dir.
        self.statusBar().showMessage("DONE!")
        os.chdir(cwd)

        moscatalogname = os.path.abspath(os.path.join(self.spec_path,moscatalogname))
        info = QMessageBox.information(self, "Status", "Catalog saved at:\n"+moscatalogname)
        
        self.close()
        
@menubar_plugin("MOSViz Table Generator (JWST/NIRSpec MSA)")
def nIRSpec_table_gen(session, data_collection):
    ex = TableGen(session.application)
    return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TableGen()
    sys.exit(app.exec_())
