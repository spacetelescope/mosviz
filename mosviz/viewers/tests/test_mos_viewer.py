from glue.core import DataCollection
from glue.app.qt.application import GlueApplication

import time

from ..mos_viewer import MOSVizViewer
import pytest

@pytest.fixture(scope='module')
def run_basic(mosviz_gui):
    mg = mosviz_gui
    return mg


def test_show_mosviz(qtbot):
    # mg = run_basic(mosviz_gui)
    # mg.show()

    dc = DataCollection([])
    ga = GlueApplication(dc)
    # qtbot.addWidget(ga)
    ga.show()
    time.sleep(5)
