from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..third_party.qtpy.QtWidgets import *

from astropy.units import spectral_density, spectral
import astropy.units as u
import numpy as np
import pyqtgraph as pg
from itertools import cycle
import logging

AVAILABLE_COLORS = cycle([(0, 0, 0), (0, 73, 73), (0, 146, 146),
                          (255, 109, 182), (255, 182, 219), (73, 0, 146),
                          (0, 109, 219), (182, 109, 255), (109, 182, 255),
                          (182, 219, 255), (146, 0, 0), (146, 73, 0),
                          (219, 209, 0), (36, 255, 36), (255, 255, 109)])


class Base1DGraph(pg.PlotWidget):
    def __init__(self, *args, **kwargs):
        super(Base1DGraph, self).__init__(*args, **kwargs)

        self._plot_item = self.getPlotItem()
        self._plot = self._plot_item.plot()

    @property
    def plot(self):
        return self._plot


class Spectrum1DGraph(Base1DGraph):
    def __init__(self, *args, **kwargs):
        super(Spectrum1DGraph, self).__init__(*args, **kwargs)