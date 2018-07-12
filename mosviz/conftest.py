# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import *

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

@pytest.fixture(scope='session')
def glue_gui():
    from glue.core import DataCollection
    from glue.app.qt.application import GlueApplication
    #
    from .viewers.mos_viewer import MOSVizViewer
#
#     import sys
    import os

    #PLAYTABLE = os.path.join("/Users/javerbukh/Documents/", "data_for_mosviz", "playdata", "jw95065-MOStable.txt")
    TESTDATA = os.path.join("/Users/javerbukh/Documents/", "data_for_mosviz", "workshop_examples", "deimos", "deimos_mosviz.tbl")

##############################

    from glue.core import data_factories

    d = data_factories.load_data(TESTDATA)
    dc = DataCollection([])
    #
    # # dc.append(d)
    #
    # ga = GlueApplication(dc)
    # ga.show()
    #
    # mosviz = ga.new_data_viewer(MOSVizViewer)
    # mosviz.add_data_for_testing(d)
    #
    # print("Viewers: ", ga.viewers)
    # print("Viewers[0][0]: ", ga.viewers[0][0])
    #
    # return mosviz
################################


    dc.append(d)
    app = GlueApplication(dc)
    # app.run_startup_action('mosviz')
    # app.load_data(d)
    app.setVisible(True)

    return app
##############################

#
#     m.add_data(d)
#
#     # mosviz = ga.new_data_viewer(MOSVizViewer)
#     sys.exit(ga.exec_())
#
#     # mosviz = MOSVizViewer(ga.session)
#     # app = create_glue_app()
#     # layout = app.tab(0)
#
#     # Cheap workaround for Windows test environment
#     # if sys.platform.startswith('win'):
#     #     layout._cubeviz_toolbar._toggle_sidebar()
#
