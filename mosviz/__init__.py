# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import absolute_import

"""
This is an Astropy affiliated package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:
    from . import loaders
    from . import viewers
    from . import widgets


def setup():
    from .viewers.mos_viewer import MOSVizViewer
    from glue.config import qt_client
    qt_client.add(MOSVizViewer)
