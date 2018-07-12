import os

from mosviz.viewers import MOSVizViewer
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

PLAYTABLE = os.path.join("/Users/javerbukh/Documents/", "data_for_mosviz", "playdata", "jw95065-MOStable.txt")

def get_mosviz_gui(glue_gui):
    print(glue_gui)
    mosviz = glue_gui.new_data_viewer(MOSVizViewer)
    # from glue.core import data_factories
    # d = data_factories.load_data(PLAYTABLE)
    # mosviz_gui.add_data_for_testing(d)
    print("Got here ###################################################")
    # qtbot.addWidget(mosviz)
    mosviz.add_data_for_testing(glue_gui.data_collection[0])
    # assert glue_gui.toolbar.source_select.currentText() == 's00001'
    return mosviz

def ttest_mosviz_gui(qtbot, mosviz_gui):
    print(mosviz_gui)
    mosviz = mosviz_gui.new_data_viewer(MOSVizViewer)
    # from glue.core import data_factories
    # d = data_factories.load_data(PLAYTABLE)
    # mosviz_gui.add_data_for_testing(d)
    print("Got here ###################################################")
    # qtbot.addWidget(mosviz)
    mosviz.add_data_for_testing(mosviz_gui.data_collection[0])
    assert mosviz_gui.toolbar.source_select.currentText() == 's00001'

def ttest_mosviz_gui2(glue_gui):
    mosviz_gui = get_mosviz_gui(glue_gui)
    print("In test 2 ################################")
    assert mosviz_gui.viewers[0][0]


def test_mosviz_gui3(glue_gui):
    mosviz_gui = get_mosviz_gui(glue_gui)
    print("In test 3 ################################")
    assert mosviz_gui.toolbar.source_select.currentText() == 's00001'

def test_mosviz_gui4(glue_gui):
    mosviz_gui = get_mosviz_gui(glue_gui)
    mosviz_gui.toolbar.cycle_next_action
    print("In test 4 ################################")
    assert mosviz_gui.toolbar.source_select.currentText() == 's00002'


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
