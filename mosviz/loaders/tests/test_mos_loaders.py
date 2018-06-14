import os

from ..jwst_loaders import (pre_nirspec_spectrum1d_reader,
                            pre_nirspec_spectrum2d_reader,
                            pre_nircam_image_reader)
from ..deimos_loaders import (deimos_spectrum1D_reader,
                              deimos_spectrum2D_reader)
from ..hst_loaders import acs_cutout_image_reader

DATA = os.path.join(os.path.dirname(__file__), 'data')

JWST1D = os.path.join(DATA, 'jwst', 'Final_spectrum_MOS_1_105_039_CLEAR-PRISM_MOS_PRISM-observation-2-c0e0_000.fits.gz')
JWST2D = os.path.join(DATA, 'jwst', '2Dspectrum_MOS_1_105_039_CLEAR-PRISM_MOS_PRISM-observation-2-c0e0_000.fits.gz')
JWSTCUTOUT = os.path.join(DATA, 'jwst', 'nrc_oct16_969.fits.gz')

DEIMOS1D = os.path.join(DATA, 'deimos', 'spec1d.1153.151.12004808.fits.gz')
DEIMOS2D = os.path.join(DATA, 'deimos', 'slit.1153.151R.fits.gz')
DEIMOSCUTOUT = os.path.join(DATA, 'deimos', '12004808.acs.v_6ac_.fits.gz')


def test_pre_nirspec_spectrum1d_reader():
    data = pre_nirspec_spectrum1d_reader(JWST1D)
    assert data.ndim == 1


def test_pre_nirspec_spectrum2d_reader():
    data = pre_nirspec_spectrum2d_reader(JWST2D)
    assert data.ndim == 2


def test_pre_nircam_image_reader():
    data = pre_nircam_image_reader(JWSTCUTOUT)
    assert data.ndim == 2


def test_deimos_spectrum1D_reader():
    data = deimos_spectrum1D_reader(DEIMOS1D)
    assert data.ndim == 1


def test_deimos_spectrum2D_reader():
    data = deimos_spectrum2D_reader(DEIMOS2D)
    assert data.ndim == 2


def test_acs_cutout_image_reader():
    data = acs_cutout_image_reader(DEIMOSCUTOUT)
    assert data.ndim == 2
