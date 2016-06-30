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


class Base2DGraph(pg.GraphicsLayoutWidget):
    def __init__(self, *args, **kwargs):
        super(Base2DGraph, self).__init__(*args, **kwargs)


class Spectrum2DGraph(Base2DGraph):
    def __init__(self, *args, **kwargs):
        super(Spectrum2DGraph, self).__init__(*args, **kwargs)


class ImageGraph(Base2DGraph):
    def __init__(self, show_iso=True):
        super(ImageGraph, self).__init__()
        self._axes = {'left': ImageAxisItem(orientation='left'),
                      'bottom': ImageAxisItem(orientation='bottom')}
        self.p1 = self.addPlot()#axisItems={'left': self._axes['left'],
                                #          'bottom': self._axes['bottom']})
        self.p1.showGrid(True, True, 0.5)
        self.vb = self.p1.getViewBox()
        self.vb.setAspectLocked()
        self.image_item = pg.ImageItem()
        self.p1.addItem(self.image_item)
        self._r1 = QGraphicsRectItem(0, 0, 0, 0)
        self.vb.addItem(self._r1)

        self.p1.disableAutoRange(self.vb.YAxis)
        self.p1.disableAutoRange(self.vb.XAxis)

        # Contrast/color control
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.image_item)

        self.iso = pg.IsocurveItem(level=0.8, pen='g')
        self.iso_line = pg.InfiniteLine(angle=0, movable=True, pen='g')

        # Isocurve drawing
        if show_iso:
            self.iso.setParentItem(self.image_item)
            self.iso.setZValue(5)

            # Draggable line for settings isocurve level
            self.hist.vb.addItem(self.iso_line)
            self.hist.vb.setMouseEnabled(y=False)
            self.iso_line.setValue(0.8)
            self.iso_line.setZValue(1000)

        def update_isocurve():
            self.iso.setLevel(self.iso_line.value())

        self.iso_line.sigDragged.connect(update_isocurve)
        self.hist.hide()

    def set_data(self, data, slit_shape=None, pix_scale=0.1):
        self.image_item.setImage(data.quantity.value)
        self.hist.setLevels(np.nanmin(data.quantity.value),
                            np.nanmax(data.quantity.value))
        self.iso.setData(pg.gaussianFilter(data.quantity.value, (2, 2)))
        self.iso_line.setValue(np.median(data.quantity.value))

        self.p1.setLabel('bottom', text="X [{}]".format(
            u.Unit(data.wcs.wcs.cunit[0])))
        self.p1.setLabel('left', text="Y [{}]".format(
            u.Unit(data.wcs.wcs.cunit[1])))

        if slit_shape is not None:
            shape = data.shape
            px_slit_shape = slit_shape[0]/pix_scale, slit_shape[1]/pix_scale

            self._r1.setRect(shape[0] * 0.5 - px_slit_shape[0] * 0.5,
                             shape[1] * 0.5 - px_slit_shape[1] * 0.5,
                             px_slit_shape[0],
                             px_slit_shape[1])
            self._r1.setPen(pg.mkPen(None))
            self._r1.setBrush(pg.mkBrush(255, 0, 0, 50))

        # self._axes['left'].update_data(pix_scale)
        # self._axes['bottom'].update_data(pix_scale)
        # _disp = data.get_dispersion().value
        # _cdisp = data.get_cross_dispersion().value
        # self.image_item.setRect(QtCore.QRect(_disp[0], _cdisp[0]), )
        # print(_disp[0], _cdisp[0])
        # self.image_item.translate(_disp[0], _cdisp[0])
        # self.image_item.scale(pix_scale, pix_scale)
        # self.p1.autoRange()

    def toggle_color_map(self, show):
        if show:
            self.addItem(self.hist)
            self.hist.show()
        else:
            self.hist.hide()
        self.removeItem(self.hist)


class ImageAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(ImageAxisItem, self).__init__(*args, **kwargs)
        self._pix_scale = None

    def update_data(self, pixel_scale):
        self._pix_scale = pixel_scale

    def tickStrings(self, values, scale, spacing):
        if self._pix_scale is not None:

            return [value * self._pix_scale for value in values]
        else:
            return super(ImageAxisItem, self).tickStrings(values, scale,
                                                          spacing)