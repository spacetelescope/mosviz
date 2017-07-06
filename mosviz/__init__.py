# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This is an Astropy affiliated package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

if not _ASTROPY_SETUP_:
    # For egg_info test builds to pass, put package imports here.
    pass


def setup():
    from .viewers.mos_viewer import MOSVizViewer
    from glue.config import qt_client

    qt_client.add(MOSVizViewer)


# Store package path information
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(ROOT_DIR, "data", "ui")
ICON_DIR = os.path.join(ROOT_DIR, "data", "ui", "icons")

