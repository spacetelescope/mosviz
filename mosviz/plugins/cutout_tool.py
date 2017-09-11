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

from astropy.table import QTable
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS, NoConvergence
from astropy.coordinates import SkyCoord
from astropy.nddata.utils import (Cutout2D, NoOverlapError)
from astropy import log
from astropy.coordinates import Angle 

from .. import UI_DIR

__all__ = ['CutoutTool','nIRSpec_cutout_tool']

class CutoutTool (QMainWindow):

    def __init__ (self, parent=None):
        super(CutoutTool,self).__init__(parent,Qt.WindowStaysOnTopHint)
        self.title = "NIRSpec Cutout Tool"
        self.spec_path = ""
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

    def initUI(self):
        path = os.path.join(UI_DIR, 'cutout_tool.ui')
        loadUi(path, self)
        self.setWindowTitle(self.title)
        self.statusBar().showMessage("Waiting for user input")

        self.progressBar.reset()
        self.inSave.setDisabled(True)

        self.inSpectra.textChanged.connect(self.update_save)
        self.start.clicked.connect(self.call_main)
        self.savePathButton.clicked.connect(self.custom_path)
        self.specBrowseButton.clicked.connect(self.get_spec_path)
        self.imageBrowseButton.clicked.connect(self.get_img_path)

        self.xSize.setText(self.cutout_x_size_default)
        self.ySize.setText(self.cutout_y_size_default)
        self.xSize.selectAll()
        self.ySize.selectAll()

        self.table_checkBox.setChecked(True)

        self.show()

    def get_spec_path(self):
        self.spec_path = compat.getexistingdirectory()
        self.inSpectra.setText(self.spec_path)
        self.update_save()

    def get_img_path(self):
        self.img_path = compat.getopenfilename(filters=" ".join(self.imageExt))[0]
        self.inImage.setText(self.img_path)

    def update_save(self):
        if not self.custom_save_path :
            self.save_path  = self.inSpectra.text() 
            if self.save_path  == "":
                self.inSave.setText("")
            else:
                self.inSave.setText(os.path.join(self.save_path ,"[Name]_cutouts",""))

    def custom_path(self):
        """
        User specified save path. Renders paths in output absolute. 
        Can also revert to default.
        """
        if self.savePathButton.text() == "Change":
            info = QMessageBox.information(self, "Info", "Changing the save destination will generate a MOSViz Table"
                                                 " that is unique to your computer (you will not be able to share it).")
        if self.custom_save_path  == False:
            self.save_path  = compat.getexistingdirectory()
            if self.save_path  == "":
                return
            self.inSave.setText(os.path.join(self.save_path ,"[Name]_cutouts",""))
            self.savePathButton.setText("Revert")
            self.custom_save_path  = True
        else:
            self.custom_save_path  = False
            self.savePathButton.setText("Change")
            self.update_save()

    def unique_id(self, ID, IDList):
        keys = IDList.keys()
        if ID not in keys:
            IDList[ID] = 0 
            return ID, IDList

        IDList[ID] += 1
        ID = ID+"-%s"%(IDList[ID])

        return ID, IDList

    def collect_text(self):
        """
        Process information in the input boxes.
        Checks if user inputs are functional.

        Returns
        -------
        userOk : bool
            True for success, False otherwise.

        """
        self.statusBar().showMessage("Reading input")
        self.spec_path = self.inSpectra.text()
        self.img_path = self.inImage.text()

        if not self.custom_save_path : #Just in case
            self.save_path  = self.spec_path  

        if self.xSize.text() != "":
            try:
                self.cutout_x_size = float(self.xSize.text())
            except ValueError:
                self.cutout_x_size = -1
        else:
            self.cutout_x_size = -1
        if self.ySize.text() != "":
            try:
                self.cutout_y_size = float(self.ySize.text())
            except ValueError:
                self.cutout_y_size = -1
        else:
            self.cutout_y_size = -1


        userOk = True #meaning did the user input correctly?

        if self.spec_path == "":
            self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.inSpectra.setStyleSheet("")

        if self.img_path == "":
            self.inImage.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.inImage.setStyleSheet("")

        if self.cutout_x_size <= 0:
            self.xSize.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.xSize.setStyleSheet("")

        if self.cutout_y_size <= 0:
            self.ySize.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.ySize.setStyleSheet("")

        if userOk:
            if not os.path.isdir(self.spec_path):
                info = QMessageBox.information(self, "Status:", 
                                               "Broken path:\n\n"+self.spec_path)
                self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False
            if not os.path.isfile(self.img_path):
                info = QMessageBox.information(self, "Status:", 
                                               "Broken path:\n\n"+self.img_path)
                self.inImage.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False


        return userOk

    #This function will be modified further to add features.
    def make_cutouts(self, imagename, table, image_label, image_ext=0, 
                     clobber=False, verbose=True):
        """
        Function to generate cutouts.
        """
        from reproject import reproject_interp
        
        with fits.open(imagename) as pf:
            data = pf[image_ext].data
            wcs = WCS(pf[image_ext].header)

        # It is more efficient to operate on an entire column at once.
        c = SkyCoord(table['ra'], table['dec'])
        x = (table['cutout_x_size'] / table['pix_scale']).value  # pix
        y = (table['cutout_y_size'] / table['pix_scale']).value  # pix
        pscl = table['pix_scale'].to(u.deg / u.pix)

        apply_rotation = False

        # Sub-directory, relative to working directory.
        path = '{0}_cutouts'.format(image_label)
        if not os.path.exists(path):
            os.mkdir(path)

        cutcls = partial(Cutout2D, data, wcs=wcs, mode='partial')

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(table)-1)
        self.progressBar.reset()
        counter = 0
        success_counter = 0 
        success_table = [False for x in range(len(table['id']))]
        print(len(table['id']))
        for position, x_pix, y_pix, pix_scl in zip(c, x, y, pscl):
            self.progressBar.setValue(counter)
            row = table[counter]
            print(row)
            print(position)
            counter += 1
            self.statusBar().showMessage("Making cutouts (%s/%s)"%(counter, len(success_table)))
            QApplication.processEvents()
            if apply_rotation:
                pix_rot = row['cutout_pa'].to(u.degree).value

                cutout_wcs = WCS(naxis=2)
                cutout_wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
                cutout_wcs.wcs.crval = [position.ra.deg, position.dec.deg]
                cutout_wcs.wcs.crpix = [(x_pix - 1) * 0.5, (y_pix - 1) * 0.5]

                try:
                    cutout_wcs.wcs.cd = wcs.wcs.cd
                    cutout_wcs.rotateCD(-pix_rot)
                except AttributeError:
                    cutout_wcs.wcs.cdelt = wcs.wcs.cdelt
                    cutout_wcs.wcs.crota = [0, -pix_rot]

                cutout_hdr = cutout_wcs.to_header()
                try:
                    cutout_arr = reproject_interp(
                        (data, wcs), cutout_hdr, shape_out=(int(np.ceil(y_pix)), int(np.ceil(x_pix))), order=2)
                except Exception:
                    if verbose:
                        log.info('reproject failed: '
                                 'Skipping {0}'.format(row['id']))
                    continue

                cutout_arr = cutout_arr[0]  # Ignore footprint
                cutout_hdr['OBJ_ROT'] = (pix_rot, 'Cutout rotation in degrees')

            else:
                try:
                    cutout = cutcls(position, size=(y_pix, x_pix))
                except NoConvergence:
                    if verbose:
                        log.info('WCS solution did not converge: '
                                 'Skipping {0}'.format(row['id']))
                    continue
                except NoOverlapError:
                    if verbose:
                        log.info('Cutout is not on image: '
                                 'Skipping {0}'.format(row['id']))
                    continue
                else:
                    cutout_hdr = cutout.wcs.to_header()
                    cutout_arr = cutout.data

            if np.array_equiv(cutout_arr, 0):
                if verbose:
                    log.info('No data in cutout: Skipping {0}'.format(row['id']))
                continue

            fname = os.path.join(
                path, '{0}_{1}_cutout.fits'.format(row['id'], image_label))

            # Construct FITS HDU.   
            hdu = fits.PrimaryHDU(cutout_arr)
            hdu.header.update(cutout_hdr)
            hdu.header['OBJ_RA'] = (position.ra.deg, 'Cutout object RA in deg')
            hdu.header['OBJ_DEC'] = (position.dec.deg, 'Cutout object DEC in deg')

            hdu.writeto(fname, overwrite=clobber)
            success_counter += 1
            success_table[counter-1] = True
            if verbose:
                log.info('Wrote {0}'.format(fname))
        
        self.progressBar.setValue(counter)
        QApplication.processEvents()
        if success_counter != len(success_table):
            with open("skipped_cutout_files.txt","w") as f:
                for i, x in enumerate(table['id']):
                    status = success_table[i]
                    if status == False:
                        f.write(table["spectrum2d"][i]+"\n")


        return success_counter, success_table
    
    def call_main(self):
        """
        Calls the main function and handles exceptions.
        """
        try:
            self.main()
        except Exception as e:
            info = QMessageBox.critical(self, "Error", str(e))
            self.close()

    def main(self):
        """
        Main function that uses information provided 
        by the user and in the headers of spectra files 
        to construct a catalog and make postage stamp cutouts.
        """
        userOK = self.collect_text() #meaning did the user input ok?
        if not userOK:
            self.statusBar().showMessage("Please fill in all fields")
            return

        self.start.setDisabled(True)
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
            self.start.setDisabled(False)
            info = QMessageBox.information(self, "Status:", "No NIRSpec files found in this directory\n"
                "File Name Format:\n\n"
                "<programName>_<objectName>_<instrument_filter>_ <grating>_<s2d|x1d>.fits")         
            return

        #Change working path to save path
        cwd = os.getcwd()
        os.chdir(self.save_path )
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

            if self.custom_save_path:
                spectrum1d = os.path.abspath(fn.replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.abspath(fn)
                cutout = os.path.join(self.save_path ,projectName+"_cutouts/"+ID+"_"+projectName+"_cutout.fits")
            else:
                spectrum1d = os.path.join(".",os.path.basename(fn).replace("s2d.fits", "x1d.fits"))
                spectrum2d = os.path.join(".",os.path.basename(fn))
                cutout = os.path.join(".",os.path.join(projectName+"_cutouts/"+ID+"_"+projectName+"_cutout.fits"))

            row.append(ID) #id
            row.append(w1) #ra
            row.append(w2) #dec
            row.append(spectrum1d) #spectrum1d
            row.append(spectrum2d) #spectrum2d
            row.append(cutout) #cutout
            row.append(0.2) #slit_width
            row.append(3.3) #slit_length
            row.append(head["CDELT2"]) #pix_scale (spatial_pixel_scale)
            row.append(self.cutout_x_size) #cutout_x_size
            row.append(self.cutout_y_size) #cutout_y_size
            row.append(head["PA_APER"]) #slit_pa

            catalog.append(row) #Add row to catalog

        #Make MOSViz Table using info in local catalog.
        self.statusBar().showMessage("Making MOSViz Table")
        colNames = ["id","ra","dec","spectrum1d","spectrum2d","cutout",
                    "slit_width","slit_length","pix_scale",
                    "cutout_x_size", "cutout_y_size", "slit_pa"]

        t = QTable(rows=catalog, names=colNames)
        t["ra"].unit = u.deg
        t["dec"].unit = u.deg
        t["slit_width"].unit = u.arcsec
        t["slit_length"].unit = u.arcsec
        t["pix_scale"].unit = (u.arcsec/u.pix)
        t["cutout_x_size"].unit = u.arcsec
        t["cutout_y_size"].unit = u.arcsec
        t["slit_pa"].unit = u.deg

        #Make cutouts using info in catalog.
        self.statusBar().showMessage("Making cutouts")
        success_counter, success_table = self.make_cutouts(self.img_path, t, projectName, clobber=True)

        #For files that do not have a cutout, place "None" as a filename place holder.
        for idx, success in enumerate(success_table):
            if not success:
                t["cutout"][idx] = "None"

        #Write MOSViz Table to file.
        self.statusBar().showMessage("Saving MOSViz Table")
        moscatalogname = os.path.join(self.save_path ,projectName+"_MOSViz_Table.txt")
        t.remove_column("cutout_x_size")
        t.remove_column("cutout_y_size")
        t.remove_column("slit_pa")
        if self.table_checkBox.isChecked():
            t.write(moscatalogname, format="ascii.ecsv", overwrite=True)

        #Change back dir.
        self.statusBar().showMessage("DONE!")
        os.chdir(cwd)

        #Give notice to user on status.
        string = "Cutouts were made for %s out of %s files\n\nSaved at: %s" %(
            success_counter,len(success_table),
            os.path.join(self.save_path ,projectName+"_cutouts/"))
        info = QMessageBox.information(self, "Status:", string)

        #If some spectra files do not have a cutout, a list of their names will be saved to
        # 'skipped_cutout_files.txt' in the save dir as the MOSViz Table file. 
        if success_counter != len(success_table):
            info = QMessageBox.information(self, "Status:", "A list of spectra files"
                                            "without cutouts is saved in"
                                            "'skipped_cutout_files.txt' at:\n\n%s"
                                            %os.path.join(self.save_path ,
                                                "skipped_cutout_files.txt"))
        self.close()
        return

@menubar_plugin("Cutout Tool (JWST/NIRSpec MSA)")
def nIRSpec_cutout_tool(session, data_collection):
    ex = CutoutTool(session.application)
    return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CutoutTool(app)
    sys.exit(app.exec_())
