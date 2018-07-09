# Licensed under a 3-clause BSD style license - see LICENSE.rst

import sys

from glue.main import main as glue_main

try:
    from glue.utils.qt.decorators import die_on_error
except ImportError:
    from glue.utils.decorators import die_on_error


@die_on_error("Error starting up MOSViz")
def main(argv=sys.argv):

    # Add startup item for MOSViz - this makes it so that the data gets
    # auto-added to the canvas.
    if '--startup=mosviz' not in argv:
        argv.append('--startup=mosviz')

    # Make sure the mosviz startup item is registered
    from .startup import mosviz_setup  # noqa

    # Launch glue
    glue_main(argv=argv)
