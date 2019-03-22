# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

# As of Astropy 3.0, the pytest plugins provided by Astropy are
# automatically made available when Astropy is installed. This means it's
# not necessary to import them here, but we still need to import global
# variables that are used for configuration.
from astropy.tests.plugins.display import PYTEST_HEADER_MODULES, TESTED_VERSIONS

## Uncomment the following line to treat all DeprecationWarnings as
## exceptions. For Astropy v2.0 or later, there are 2 additional keywords,
## as follow (although default should work for most cases).
## To ignore some packages that produce deprecation warnings on import
## (in addition to 'compiler', 'scipy', 'pygments', 'ipykernel', and
## 'setuptools'), add:
##     modules_to_ignore_on_import=['module_1', 'module_2']
## To ignore some specific deprecation warning messages for Python version
## MAJOR.MINOR or later, add:
##     warnings_to_ignore_by_pyver={(MAJOR, MINOR): ['Message to ignore']}
# from astropy.tests.helper import enable_deprecations_as_exceptions
# enable_deprecations_as_exceptions()

## Uncomment and customize the following lines to add/remove entries from
## the list of packages for which version numbers are displayed when running
## the tests. Making it pass for KeyError is essential in some cases when
## the package uses other astropy affiliated packages.
# try:
#     PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
#     PYTEST_HEADER_MODULES['scikit-image'] = 'skimage'
#     del PYTEST_HEADER_MODULES['h5py']
# except (NameError, KeyError):  # NameError is needed to support Astropy < 1.0
#     pass

## Uncomment the following lines to display the version number of the
## package rather than the version number of Astropy in the top line when
## running the tests.
# import os
#
## This is to figure out the affiliated package version, rather than
## using Astropy's
import pytest

try:
    from .version import version
except ImportError:
    version = 'dev'

try:
    packagename = os.path.basename(os.path.dirname(__file__))
    TESTED_VERSIONS[packagename] = version
except NameError:   # Needed to support Astropy <= 1.0.0
    pass

import os

from glue.core import DataCollection
from glue.app.qt.application import GlueApplication
from glue.core import data_factories

from .viewers.mos_viewer import MOSVizViewer

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'tests', 'data')
DEIMOSTABLE = os.path.join(TEST_DATA_DIR, 'deimos_mosviz.tbl')


if not os.environ.get('JWST_DATA_TEST', False):
    @pytest.fixture(scope='session')
    def glue_gui():

        d = data_factories.load_data(DEIMOSTABLE)
        dc = DataCollection([])
        dc.append(d)

        # Creates glue instance
        app = GlueApplication(dc)
        app.setVisible(True)

        # Adds data to the MosVizViewer
        app.new_data_viewer(MOSVizViewer)
        app.viewers[0][0].add_data_for_testing(app.data_collection[0])

        return app


    @pytest.fixture(autouse=True)
    def reset_state(glue_gui):
        # This yields the test itself
        yield

        # Returns the applications to this state between tests
        # Currently, this only changes the index of the comboboxes back to 0.
        # TODO: In the future, this may need to be more robust
        reset_mosviz = glue_gui.viewers[0][0]
        reset_mosviz.toolbar.source_select.setCurrentIndex(0)
        reset_mosviz.toolbar.exposure_select.setCurrentIndex(0)
