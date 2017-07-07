from glue.core import DataCollection
from glue.app.qt.application import GlueApplication

from ..mos_viewer import MOSVizViewer


def test_basic():
    dc = DataCollection([])
    ga = GlueApplication(dc)
    mosviz = ga.new_data_viewer(MOSVizViewer)
    mosviz.show()
