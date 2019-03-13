# Licensed under a 3-clause BSD style license - see LICENSE.rst

import sys
import os
import argparse

import glue
from glue.utils.qt import get_qapp
from glue.app.qt import GlueApplication
from glue.main import get_splash, load_data_files, load_plugins
from qtpy.QtCore import QTimer
from qtpy import QtGui, QtWidgets

from .plugins.cutout_tool import nIRSpec_cutout_tool
from .plugins.cutout_tool import general_cutout_tool
from .plugins.table_generator import nIRSpec_table_gen
from mosviz import __version__

try:
    from glue.utils.qt.decorators import die_on_error
except ImportError:
    from glue.utils.decorators import die_on_error



MOSVIZ_ICON_PATH = os.path.abspath(
    os.path.join(
        os.path.abspath(__file__),
        "..",
        "data",
        "resources",
        "mosviz_icon.png"
    )
)

MOSVIZ_SPLASH_PATH = os.path.abspath(
    os.path.join(
        os.path.abspath(__file__),
        "..",
        "data",
        "resources",
        "mosviz_splash.png"
    )
)


@die_on_error("Error starting up MOSViz")
def main(argv=sys.argv):
    """
    The majority of the code in this function was taken from start_glue() in main.py after a discussion with
    Tom Robataille. We wanted the ability to get command line arguments and use them in here and this seemed
    to be the cleanest way to do it.
    """
    # Make sure the mosviz startup item is registered
    from .startup import mosviz_setup  # noqa

    parser = argparse.ArgumentParser()
    parser.add_argument('data_files', nargs=argparse.REMAINDER)
    args = parser.parse_known_args(argv[1:])

    datafiles = args[0].data_files

    ga = create_app(datafiles, interactive=True)

    ga.start(maximized=True)


def _create_glue_app(data_collection, hub):
    session = glue.core.Session(data_collection=data_collection, hub=hub)
    ga = GlueApplication(session=session)
    qapp = QtWidgets.QApplication.instance()
    ga.setWindowTitle('MOSViz v{0}'.format(__version__))
    qapp.setWindowIcon(QtGui.QIcon(MOSVIZ_ICON_PATH))
    ga.setWindowIcon(QtGui.QIcon(MOSVIZ_ICON_PATH))
    return ga


def create_app(datafiles=[], interactive=True):

    app = get_qapp()

    if interactive:
        # Splash screen
        splash = get_splash()
        splash.image = QtGui.QPixmap(MOSVIZ_SPLASH_PATH)
        splash.show()
    else:
        splash = None

    # Start off by loading plugins. We need to do this before restoring
    # the session or loading the configuration since these may use existing
    # plugins.
    load_plugins(splash=splash)

    # # Show the splash screen for 2 seconds
    if interactive:
        timer = QTimer()
        timer.setInterval(2000)
        timer.setSingleShot(True)
        timer.timeout.connect(splash.close)
        timer.start()

    data_collection = glue.core.DataCollection()
    hub = data_collection.hub

    if interactive:
        splash.set_progress(100)

    ga = _create_glue_app(data_collection, hub)
    ga.run_startup_action('mosviz')

    # Load the data files.
    if datafiles:
        datasets = load_data_files(datafiles)
        ga.add_datasets(data_collection, datasets, auto_merge=False)

    return ga
