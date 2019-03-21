# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This is an Astropy affiliated package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

import sys
from pkg_resources import get_distribution, DistributionNotFound

# This *must* occur before any imports from glue. It prevents the "python must
# be installed as a framework" error that occurs on OSX. Since we now
# explicitly depend on PyQt5, we use it as the mpl backend.
import matplotlib as mpl
mpl.use('Qt5Agg')

from .mosviz_data_factory import *

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"


__minimum_python_version__ = "3.6"

class UnsupportedPythonError(Exception):
    pass

# Enforce Python version check during package import.
if sys.version_info < tuple((int(val) for val in __minimum_python_version__.split('.'))):
    raise UnsupportedPythonError("mosviz does not support Python < {}".format(__minimum_python_version__))


def setup():
    from .viewers.mos_viewer import MOSVizViewer
    from glue.config import qt_client
    from .plugins.cutout_tool import nIRSpec_cutout_tool
    from .plugins.cutout_tool import general_cutout_tool
    from .plugins.table_generator import nIRSpec_table_gen
    from .startup import mosviz_setup
    qt_client.add(MOSVizViewer)


# Store package path information
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(ROOT_DIR, "data", "ui")
ICON_DIR = os.path.join(ROOT_DIR, "data", "ui", "icons")

