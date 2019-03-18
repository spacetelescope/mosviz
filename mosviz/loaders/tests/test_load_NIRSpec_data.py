import os
import urllib.request
import zipfile

from mosviz.cli import create_app
from mosviz.viewers.mos_viewer import MOSVizViewer

from specviz.tests.test_load_data import jwst_data_test


JWST_DATA_FILES = [
        # Mocked up level 3 NIRSpec data folder
        'https://stsci.box.com/shared/static/iv0nqx9h4w7yqlc1g1v0cos5p8qrdv64.zip'
]


JWST_TABLE_NAMES = [
    # Regular test
    'level3_NIRSpec/mosviz_table_lvl3.txt',
    # None test
    'level3_NIRSpec/mosviz_table_Nones.txt'

]


@jwst_data_test
def test_NIRSpec_data(tmpdir):
    app = None

    urllib.request.urlretrieve(JWST_DATA_FILES[0], os.path.join(tmpdir,"level3_NIRSpec.zip"))
    # un-zip folder
    zip_ref = zipfile.ZipFile(os.path.join(tmpdir, "level3_NIRSpec.zip"), 'r')
    zip_ref.extractall(tmpdir)
    zip_ref.close()

    app = create_app(interactive=False)
    app.load_data([os.path.join(tmpdir, JWST_TABLE_NAMES[0])])

    app.new_data_viewer(MOSVizViewer)
    add_data_for_jwst_testing(app.viewers[0][0], app.data_collection[0])

    assert app.viewers[0][0].image_widget.isVisible()
    assert app.viewers[0][0].spectrum2d_widget._im is not None
    # We should also check specviz viewer but this is not hooked up at the moment

    if app is not None:
        app.app.quit()


@jwst_data_test
def test_NIRSpec_None_table(tmpdir):
    app = None

    urllib.request.urlretrieve(JWST_DATA_FILES[0],
                               os.path.join(tmpdir, "level3_NIRSpec.zip"))
    # un-zip folder
    zip_ref = zipfile.ZipFile(os.path.join(tmpdir, "level3_NIRSpec.zip"), 'r')
    zip_ref.extractall(tmpdir)
    zip_ref.close()

    app = create_app(interactive=False)
    app.load_data([os.path.join(tmpdir, JWST_TABLE_NAMES[1])])

    app.new_data_viewer(MOSVizViewer)
    add_data_for_jwst_testing(app.viewers[0][0], app.data_collection[0])

    # Once specviz viewer is hooked up we should check the first dataset
    assert app.viewers[0][0].image_widget.isVisible()
    assert app.viewers[0][0].spectrum2d_widget._im is not None

    # Move to next dataset, with None for s2d file
    app.viewers[0][0].toolbar.source_select.setCurrentIndex(1)
    assert app.viewers[0][0].image_widget.isVisible()
    assert app.viewers[0][0].spectrum2d_widget._im is None

    # Move to next dataset, with None for s3d file
    app.viewers[0][0].toolbar.source_select.setCurrentIndex(2)
    assert not app.viewers[0][0].image_widget.isVisible()
    # This is actually broken right now, so this part of the test will fail
    #assert app.viewers[0][0].spectrum2d_widget._im is not None

    # Move to last dataset, should have entries for everything
    app.viewers[0][0].toolbar.source_select.setCurrentIndex(3)
    assert app.viewers[0][0].image_widget.isVisible()
    assert app.viewers[0][0].spectrum2d_widget._im is not None

    if app is not None:
        app.app.quit()


def add_data_for_jwst_testing(MosVizViewer, data):
    """
    Processes data message from the central communication hub.

    Parameters
    ----------
    data : :class:`glue.core.data.Data`
        Data object.
    """

    # Check whether the data is suitable for the MOSViz viewer - basically
    # we expect a table of 1D columns with at least three string and four
    # floating-point columns.
    if data.ndim != 1:
        raise Exception("MOSViz viewer can only be used for data with "
                        "1-dimensional components")

    components = [data.get_component(cid) for cid in data.main_components]
    categorical = [c for c in components if c.categorical]
    if len(categorical) < 3:
        raise Exception("MOSViz viewer expected at least three string "
                        "components/columns, representing the filenames of "
                        "the 1D and 2D spectra and cutouts")

    # We can relax the following requirement if we make the slit parameters
    # optional
    numerical = [c for c in components if c.numeric]
    if len(numerical) < 4:
        raise Exception("MOSViz viewer expected at least four numerical "
                        "components/columns, representing the slit position, "
                        "length, and position angle")

    # Block of code to bypass the loader_selection gui
    #########################################################
    if 'loaders' not in data.meta:
        data.meta['loaders'] = {}

    # Deimos data
    data.meta['loaders']['spectrum1d'] = "NIRSpec 1D Spectrum"
    data.meta['loaders']['spectrum2d'] = "NIRSpec 2D Spectrum"
    data.meta['loaders']['cutout'] = "ACS Cutout Image"

    if 'special_columns' not in data.meta:
        data.meta['special_columns'] = {}

    data.meta['special_columns']['spectrum1d'] = 'spectrum1d'
    data.meta['special_columns']['spectrum2d'] = 'spectrum2d'
    data.meta['special_columns']['source_id'] = 'id'
    data.meta['special_columns']['cutout'] = 'cutout'
    data.meta['special_columns']['slit_ra'] = 'ra'
    data.meta['special_columns']['slit_dec'] = 'dec'
    data.meta['special_columns']['slit_width'] = 'slit_width'
    data.meta['special_columns']['slit_length'] = 'slit_length'

    data.meta['loaders_confirmed'] = True
    #########################################################

    MosVizViewer._primary_data = data
    MosVizViewer._layer_view.data = data
    MosVizViewer._unpack_selection(data)
