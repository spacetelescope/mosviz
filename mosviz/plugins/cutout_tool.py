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

class cutoutTool (QMainWindow):

    def __init__ (self, parent=None):
        super(cutoutTool,self).__init__(parent,Qt.WindowStaysOnTopHint)
        self.title = "NIRSpec Cutout Tool"
        self.specPath = ""
        self.imgPath = ""
        self.savePath = ""
        self.cutout_x_size = 0
        self.cutout_y_size = 0
        self.cutout_x_size_default = ""
        self.cutout_y_size_default = ""
        self.customSavePath = False
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
        self.start.clicked.connect(self.main)
        self.savePathButton.clicked.connect(self.custom_path)
        self.specBrowseButton.clicked.connect(self.get_spec_path)
        self.imageBrowseButton.clicked.connect(self.get_img_path)

        self.xSize.setText(self.cutout_x_size_default)
        self.ySize.setText(self.cutout_y_size_default)
        self.xSize.selectAll()
        self.ySize.selectAll()

        self.show()

    def get_spec_path(self):
        self.specPath = compat.getexistingdirectory()
        self.inSpectra.setText(self.specPath)
        self.update_save()

    def get_img_path(self):
        self.imgPath = compat.getopenfilename(filters=" ".join(self.imageExt))[0]
        self.inImage.setText(self.imgPath)

    def update_save(self):
        if not self.customSavePath:
            self.savePath = self.inSpectra.text() 
            if self.savePath == "":
                self.inSave.setText("")
            else:
                self.inSave.setText(os.path.join(self.savePath,"[Name]_cutouts",""))

    def custom_path(self):
        info = "Changing the default save path will result in absolute paths to be saved into the MOSViz Table."
        info+= "This means the MOSViz Table will only work on your computer and cannot be shared."
        info = QMessageBox.information(self, "Status:", info)
        if self.customSavePath == False:
            self.savePath = compat.getexistingdirectory()
            if self.savePath == "":
                return
            self.inSave.setText(os.path.join(self.savePath,"[Name]_cutouts",""))
            self.savePathButton.setText("Revert")
            self.customSavePath = True
        else:
            self.customSavePath = False
            self.savePathButton.setText("Change")
            self.update_save()


    def collect_text(self):
        self.statusBar().showMessage("Reading input")
        self.specPath = self.inSpectra.text()
        self.imgPath = self.inImage.text()

        if not self.customSavePath: #Just in case
            self.savePath = self.specPath  

        if self.xSize.text() != "":
            self.cutout_x_size = float(self.xSize.text())
        else:
            self.cutout_x_size = 0
        if self.ySize.text() != "":
            self.cutout_y_size = float(self.ySize.text())
        else:
            self.cutout_y_size = 0


        userOk = True #meaning did the user input?

        if self.specPath == "":
            self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
            userOk = False
        else:
            self.inSpectra.setStyleSheet("")

        if self.imgPath == "":
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
            if not os.path.isdir(self.specPath):
                info = "Broken path:\n\n"
                info+= self.specPath
                info = QMessageBox.information(self, "Status:", info)
                self.inSpectra.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False
            if not os.path.isfile(self.imgPath):
                info = "Broken path:\n\n"
                info+= self.imgPath
                info = QMessageBox.information(self, "Status:", info)
                self.inImage.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
                userOk = False


        return userOk

    def make_cutouts(self,imagename, catalog, image_label, image_ext=0, clobber=False, verbose=True):
        from reproject import reproject_interp

        table = QTable()
        table['id'] = catalog['id']['data']
        table['ra'] = catalog['ra']['data']*catalog['ra']['unit']
        table['dec'] = catalog['dec']['data']*catalog['dec']['unit']
        table['cutout_x_size'] = catalog['cutout_x_size']['data']*catalog['cutout_x_size']['unit']
        table['cutout_y_size'] = catalog['cutout_y_size']['data']*catalog['cutout_y_size']['unit']
        table['spatial_pixel_scale'] = catalog['spatial_pixel_scale']['data']*catalog['spatial_pixel_scale']['unit']
        table['cutout_pa'] = catalog['slit_pa']['data']*catalog['slit_pa']['unit']
        table['slit_width'] = catalog['slit_width']['data']*catalog['slit_width']['unit']
        table['slit_length'] = catalog['slit_length']['data']*catalog['slit_length']['unit']
        
        with fits.open(imagename) as pf:
            data = pf[image_ext].data
            wcs = WCS(pf[image_ext].header)

        # It is more efficient to operate on an entire column at once.
        c = SkyCoord(table['ra'], table['dec'])
        x = (table['cutout_x_size'] / table['spatial_pixel_scale']).value  # pix
        y = (table['cutout_y_size'] / table['spatial_pixel_scale']).value  # pix
        pscl = table['spatial_pixel_scale'].to(u.deg / u.pix)

        apply_rotation = False

        # Sub-directory, relative to working directory.
        path = '{0}_cutouts'.format(image_label)
        if not os.path.exists(path):
            os.mkdir(path)

        cutcls = partial(Cutout2D, data, wcs=wcs, mode='partial')

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(catalog['id']['data'])-1)
        self.progressBar.reset()
        counter = 0
        success_counter = 0 
        success_table = [False for x in catalog['id']['data']]
        for position, x_pix, y_pix, pix_scl, row in zip(c, x, y, pscl, table):
            self.progressBar.setValue(counter)
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
                for i, x in enumerate(catalog['id']['data']):
                    status = success_table[i]
                    if status == False:
                        f.write(catalog["spectrum2d"]["data"][i]+"\n")


        return success_counter, success_table
            

    def main(self):
        userOK = self.collect_text() #meaning did the user input ok?
        if not userOK:
            self.statusBar().showMessage("Please fill in all fields")
            return

        self.start.setDisabled(True)
        self.statusBar().showMessage("Making a list of files")
        
        
        target_names = []
        fb = [] # File Base
        searchPath = os.path.join(self.specPath,"*s2d.fits")
        for fn in glob(searchPath):
            name = os.path.basename(fn)
            name = name.split("_") #Split up file name
            if len(name) != 5:
                continue
            name = name[-4] # Get the target name from file
            target_names.append(name)
            fb.append(fn)
            

        if len(fb) == 0:
            self.statusBar().showMessage("NIRSpec files not found")
            self.start.setDisabled(False)
            info = "No NIRSpec files found in this directory\n"
            info+= "File Name Format:\n\n"
            info+= "programName_objectName_instrument_filter_ grating_(s2d|x1d).fits"
            info = QMessageBox.information(self, "Status:", info)
            
            return

        cwd = os.getcwd()
        os.chdir(self.savePath)
        self.statusBar().showMessage("Making catalog")

        catalog = {}
        catalog["id"] = {"name": "id", "datatype": "str", "data": []}
        catalog["ra"] = {"name": "ra", "unit": u.deg, "datatype": "float64", "data": []}
        catalog["dec"] = {"name": "dec", "unit": u.deg, "datatype": "float64", "data": []}
        catalog["cutout_x_size"] = {"name": "cutout_x_size", "unit": u.arcsec, "datatype": "float64", "data": []}
        catalog["cutout_y_size"] = {"name": "cutout_y_size", "unit": u.arcsec, "datatype": "float64", "data": []}
        catalog["spatial_pixel_scale"] ={"name": "spatial_pixel_scale", "unit": u.arcsec / u.pix, "datatype": "float64", "data": []}
        catalog["slit_pa"] = {"name": "slit_pa", "unit": u.deg, "datatype": "float64", "data": []}
        catalog["slit_width"] = {"name": "slit_width", "unit": u.arcsec, "datatype": "float64", "data": []}
        catalog["slit_length"] = {"name": "slit_length", "unit": u.arcsec, "datatype": "float64", "data": []}
        catalog["spectrum1d"] = {"name": "spectrum1d", "datatype": "str", "data": []}
        catalog["spectrum2d"] = {"name": "spectrum2d", "datatype": "str", "data": []}
        catalog["cutout"] = {"name": "cutout", "datatype": "string", "data": []}

        projectName = os.path.basename(fn).split("_")[0]
        for idx, fn in enumerate(fb): #Fore file name in file base:
            headx1d = fits.open(fn.replace("s2d.fits", "x1d.fits"))['extract1d'].header
            wcs = WCS(headx1d)
            w1, w2 = wcs.wcs_pix2world(0., 0., 1)
            w1 = w1.tolist()
            w2 = w2.tolist()

            head = fits.getheader(fn)
            ID = target_names[idx]
            catalog["id"]["data"].append(ID)
            catalog["ra"]["data"].append(w1)#rn.uniform(359.999, 359.980393928))#head["TARG_RA"]
            catalog["dec"]["data"].append(w2)#rn.uniform(0.0197402256312, 0.00394170958794))#head["TARG_DEC"]
            catalog["cutout_x_size"]["data"].append(self.cutout_x_size)
            catalog["cutout_y_size"]["data"].append(self.cutout_y_size)
            catalog["spatial_pixel_scale"]["data"].append(head["CDELT2"])
            catalog["slit_pa"]["data"].append(head["PA_APER"]) #todo check this because it might be none
            catalog["slit_width"]["data"].append(0.2)
            catalog["slit_length"]["data"].append(3.3)
            if self.customSavePath:
                catalog["spectrum1d"]["data"].append(fn.replace("s2d.fits", "x1d.fits"))
                catalog["spectrum2d"]["data"].append(fn)
                catalog["cutout"]["data"].append(os.path.join(self.savePath,projectName+"_cutouts/"+ID+"_"+projectName+"_cutout.fits"))
            else:
                catalog["spectrum1d"]["data"].append(os.path.join(".",os.path.basename(fn).replace("s2d.fits", "x1d.fits")))
                catalog["spectrum2d"]["data"].append(os.path.join(".",os.path.basename(fn)))
                catalog["cutout"]["data"].append(os.path.join(".",os.path.join(projectName+"_cutouts/"+ID+"_"+projectName+"_cutout.fits")))

        self.statusBar().showMessage("Making cutouts")
        
        success_counter, success_table = self.make_cutouts(self.imgPath, catalog, projectName, clobber=True)
        
        #self.make_cutouts(self.imgPath, catalog, projectName, clobber=True)
        for idx, success in enumerate(success_table):
            if not success:
                catalog["cutout"]["data"][idx] = "None"

        self.statusBar().showMessage("Making MOSViz catalog")
        moscatalog = ["# %ECSV 0.9\n"+
        "# ---\n"+
        "# datatype:\n"+
        "# - {name: id, datatype: string}\n"+
        "# - {name: ra, unit: deg, datatype: float64}\n"+
        "# - {name: dec, unit: deg, datatype: float64}\n"+
        "# - {name: spectrum1d, datatype: string}\n"+
        "# - {name: spectrum2d, datatype: string}\n"+
        "# - {name: cutout, datatype: string}\n"+
        "# - {name: slit_width, unit: arcsec, datatype: float64}\n"+
        "# - {name: slit_length, unit: arcsec, datatype: float64}\n"+
        "# - {name: pix_scale, unit: arcsec / pix, datatype: float64}\n"+
        "# - {name: flag, datatype: string}\n"+
        "# - {name: comments, datatype: string}\n"+
        "id ra dec spectrum1d spectrum2d cutout slit_width slit_length pix_scale\n"]

        for i, fn in enumerate(fb):
            ID = catalog["id"]["data"][i]
            ra = "%.10f"%(catalog["ra"]["data"][i])
            dec = "%.10f"%(catalog["dec"]["data"][i])
            spectrum1d = catalog["spectrum1d"]["data"][i] 
            spectrum2d = catalog["spectrum2d"]["data"][i] 
            cutout = catalog["cutout"]["data"][i]
            slit_width =  "%.10f"%(catalog["slit_width"]["data"][i])
            slit_length = "%.10f"%(catalog["slit_length"]["data"][i])
            pix_scale = "%.10f"%(catalog["spatial_pixel_scale"]["data"][i])

            moscatalog.append(ID+" "+ra+" "+dec+" "+spectrum1d+" "+
                spectrum2d+" "+cutout+" "+slit_width+" "
                +slit_length+" "+pix_scale+"\n")

        self.statusBar().showMessage("Saving MOSViz catalog")
        #moscatalogname = self.savePath+projectName+"-MOStable.txt"
        moscatalogname = os.path.join(self.savePath,projectName+"_MOSViz_Table.txt")
        with open(moscatalogname,"w") as f:
            for line in moscatalog:
                f.write(line)
            
        self.statusBar().showMessage("DONE!")
        os.chdir(cwd)

        info = "Cutouts were made for %s out of %s files\n\nSaved at: %s" %(
            success_counter,len(set(target_names)),
            os.path.join(self.savePath,projectName+"_cutouts/"))
        info = QMessageBox.information(self, "Status:", info)

        if success_counter != len(set(target_names)):
            info = "A list of spectra files without cutouts is saved in 'skipped_cutout_files.txt' at:\n\n"
            info += os.path.join(self.savePath,"skipped_cutout_files.txt")
            info = QMessageBox.information(self, "Status:", info)

        self.close()
        return

@menubar_plugin("NIRSpec Cutout Tool")
def nIRSpec_cutout_tool(session, data_collection):
    ex = cutoutTool(session.application)
    return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = cutoutTool(app)
    sys.exit(app.exec_())
