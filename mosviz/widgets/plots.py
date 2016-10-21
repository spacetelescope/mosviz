from qtpy.QtWidgets import QMainWindow

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from glue.viewers.image.qt.viewer_widget import StandaloneImageWidget


class Line1DWidget(QMainWindow):
    def __init__(self, parent=None):
        super(Line1DWidget, self).__init__(parent)

        self.figure = plt.figure(facecolor='white')

        # Canvas Widget that displays the `figure` it takes the `figure`
        # instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # Navigation widget, it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.canvas)

        self._axes = None

    @property
    def axes(self):
        return self._axes

    def set_data(self, x, y, yerr=None):
        # Create an axis
        self._axes = self.figure.add_subplot(111)

        # Discards the old graph
        self._axes.hold(False)

        # Plot data
        if yerr is None:
            self._axes.plot(x, y)
        else:
            self._axes.errorbar(x, y, yerr=yerr)

        # Refresh canvas
        self.canvas.draw()


class ShareableAxesImageWidget(StandaloneImageWidget):
    def __init__(self, *args, **kwargs):
        super(ShareableAxesImageWidget, self).__init__(*args, **kwargs)

    def set_image(self, share_x=None, share_y=None, **kwargs):
        self._axes._sharex = share_x
        self._axes._sharey = share_y

        super(ShareableAxesImageWidget, self).set_image(**kwargs)