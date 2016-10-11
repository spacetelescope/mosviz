from qtpy.QtWidgets import QMainWindow

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


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

        self.set_data()

    def set_data(self, data):
        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.hold(False)

        # plot data
        ax.plot(data, '*-')

        # refresh canvas
        self.canvas.draw()
