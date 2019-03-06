import pytest
import tempfile
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal, assert_almost_equal

from mosviz.plugins.cutout_tool.cutout_lib import make_cutouts, cutouts_from_fits

from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.io import fits
from astropy.io.fits.tests import FitsTestCase
from astropy.table import Table
from astropy.nddata import NDData


class TestCutoutTools(FitsTestCase):
    def setup(self):
        self.temp_dir = tempfile.mkdtemp(prefix='fits-test-')
        fits.conf.enable_record_valued_keyword_cards = True
        fits.conf.extension_name_case_sensitive = False
        fits.conf.strip_header_whitespace = True
        fits.conf.use_memmap = True

    @staticmethod
    def construct_test_image():
        # Construct data: 9 X 9 array where
        # the value at each pixel (x, y) is x*10 + y
        data = np.array([i * 9 + np.arange(9) for i in range(9)])

        # Construct a WCS for test image
        # N.B: Pixel scale should be 1 deg/pix
        w = WCS()
        w.wcs.crpix = [5, 5]
        w.wcs.crval = [0, 45]
        w.wcs.cdelt = [-1, 1]
        w.wcs.ctype = ['RA---TAN', 'DEC--TAN']

        # Construct fits header
        h = w.to_header()

        # Construct Image and return:
        return fits.PrimaryHDU(data, h)

    def test_make_cutouts_inputs(self):
        # Construct image:
        image_hdu = self.construct_test_image()

        # Construct catalog
        ra = [0, 1] * u.deg
        dec = [45, 46] * u.deg
        ids = ["Target_1", "Target_2"]
        cutout_width = cutout_height = [4.0, 4.0] * u.pix

        catalog = Table(
            data=[ids, ra, dec, cutout_width, cutout_height],
            names=['id', 'ra', 'dec', 'cutout_width', 'cutout_height'])

        # From NumPy Array and WCS:
        array = image_hdu.data
        w = WCS(image_hdu.header)
        assert None not in make_cutouts(array, catalog, wcs=w)

        # From NDData Array Only:
        w = WCS(image_hdu.header)
        array = NDData(data=image_hdu.data, wcs=w)
        assert None not in make_cutouts(array, catalog)

    def test_cutouts_from_fits_inputs(self):
        # Construct image:
        image_hdu = self.construct_test_image()

        # Construct catalog
        ra = [0, 1] * u.deg
        dec = [45, 46] * u.deg
        ids = ["Target_1", "Target_2"]
        cutout_width = cutout_height = [4.0, 4.0] * u.pix

        catalog = Table(
            data=[ids, ra, dec, cutout_width, cutout_height],
            names=['id', 'ra', 'dec', 'cutout_width', 'cutout_height'])

        # Test with no rotation

        # - From memory:
        assert None not in cutouts_from_fits(image_hdu, catalog)

        # - From fits file:
        fits_file = self.temp("input_image.fits")
        image_hdu.writeto(fits_file)
        assert None not in cutouts_from_fits(fits_file, catalog)

        # - From HDUList:
        hdu_list = fits.HDUList(image_hdu)
        assert None not in cutouts_from_fits(hdu_list, catalog)

        # - From ECSV file
        ecsv_file = self.temp("input_catalog.ecsv")
        catalog.write(ecsv_file, format="ascii.ecsv")
        assert None not in cutouts_from_fits(image_hdu, ecsv_file)

        # Test with rotation column:
        pa = [90, 45] * u.deg
        catalog.add_column(pa, name="cutout_pa")
        assert None not in cutouts_from_fits(image_hdu, catalog)

    def test_cutout_tool_correctness(self):
        # Construct image:
        image_hdu = self.construct_test_image()

        # Construct catalog
        ra = [0] * u.deg  # Center pixel
        dec = [45] * u.deg  # Center pixel
        ids = ["target_1"]

        # Cutout should be 3 by 3:
        cutout_width = cutout_height = [3.0] * u.pix

        catalog = Table(
            data=[ids, ra, dec, cutout_width, cutout_height],
            names=['id', 'ra', 'dec', 'cutout_width', 'cutout_height'])

        # Call cutout tool and extract the first cutout:
        cutout = cutouts_from_fits(image_hdu, catalog)[0]

        # check if values are correct:
        w_orig = WCS(image_hdu.header)
        w_new = WCS(cutout.header)

        for x_new, x_orig in enumerate(range(3, 6)):
            for y_new, y_orig in enumerate(range(3, 6)):
                coords_orig = SkyCoord.from_pixel(x_orig, y_orig, w_orig, origin=0)
                coords_new = SkyCoord.from_pixel(x_new, y_new, w_new, origin=0)

                assert_almost_equal(image_hdu.data[x_orig][y_orig], cutout.data[x_new][y_new])
                assert_almost_equal(coords_orig.ra.value, coords_new.ra.value)
                assert_almost_equal(coords_orig.dec.value, coords_new.dec.value)

        # Test for rotation:
        pa = [180] * u.deg
        catalog.add_column(pa, name="cutout_pa")

        # Call cutout tool:
        cutout = cutouts_from_fits(image_hdu, catalog)[0]

        # check if values are correct:
        w_orig = WCS(image_hdu.header)
        w_new = WCS(cutout.header)

        for x_new, x_orig in enumerate(range(5, 2, -1)):
            for y_new, y_orig in enumerate(range(5, 2, -1)):
                coords_orig = SkyCoord.from_pixel(x_orig, y_orig, w_orig, origin=0)
                coords_new = SkyCoord.from_pixel(x_new, y_new, w_new, origin=0)

                assert_almost_equal(image_hdu.data[x_orig][y_orig], cutout.data[x_new][y_new])
                assert_almost_equal(coords_orig.ra.value, coords_new.ra.value)
                assert_almost_equal(coords_orig.dec.value, coords_new.dec.value)