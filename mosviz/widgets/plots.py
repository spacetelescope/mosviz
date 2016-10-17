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

    def set_data(self, x, y, yerr=None):
        # print(data)
        # Create an axis
        ax = self.figure.add_subplot(111)

        # Discards the old graph
        ax.hold(False)

        # Plot data
        if yerr is None:
            ax.plot(x, y)
        else:
            ax.errorbar(x, y, yerr=1/yerr)

        # Refresh canvas
        self.canvas.draw()
