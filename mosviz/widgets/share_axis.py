# This provides a helper class that can be used to link the limits of axes

from glue.utils.matplotlib import defer_draw
from glue.utils.decorators import avoid_circular

__all__ = ['SharedAxisHelper']


class SharedAxisHelper(object):
    """
    A helper class that can be used to enable/disable sharing of the x and/or y
    axis between two Axes. This is needed because Matplotlib does not have a
    public API for enabling sharing on axes after initialization, and using
    events as below is preferable compared to accessing the private _sharex or
    _sharey attributes on Axes classes since the private attributes are not
    guaranteed to exist in future.
    """

    def __init__(self, axes1, axes2, sharex=False, sharey=False):
        self._axes1 = axes1
        self._axes2 = axes2
        self._sharex = sharex
        self._sharey = sharey
        self._axes1.callbacks.connect('xlim_changed', self._on_xlim_change)
        self._axes1.callbacks.connect('ylim_changed', self._on_ylim_change)
        self._axes2.callbacks.connect('xlim_changed', self._on_xlim_change)
        self._axes2.callbacks.connect('ylim_changed', self._on_ylim_change)

    @property
    def sharex(self):
        return self._sharex

    @sharex.setter
    def sharex(self, value):
        self._sharex = value
        self._on_xlim_change(self._axes1)
        self._axes1.figure.canvas.draw()

    @property
    def sharey(self):
        return self._sharex

    @sharey.setter
    def sharey(self, value):
        self._sharey = value
        self._on_ylim_change(self._axes1)
        self._axes1.figure.canvas.draw()

    @defer_draw
    @avoid_circular
    def _on_xlim_change(self, axes):
        print('_on_xlim_change', axes, self._sharex)
        if self._sharex:
            if axes is self._axes1:
                self._axes2.set_xlim(*self._axes1.get_xlim())
                self._axes2.figure.canvas.draw()
            else:
                self._axes1.set_xlim(*self._axes2.get_xlim())
                self._axes1.figure.canvas.draw()

    @defer_draw
    @avoid_circular
    def _on_ylim_change(self, axes):
        print('_on_ylim_change', axes, self._sharey)
        if self._sharey:
            if axes is self._axes1:
                self._axes2.set_ylim(*self._axes1.get_ylim())
                self._axes2.figure.canvas.draw()
            else:
                self._axes1.set_ylim(*self._axes2.get_ylim())
                self._axes1.figure.canvas.draw()


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    fig = plt.figure()

    subplot = 1

    helpers = []

    for sharex in [False, True]:
        for sharey in [False, True]:
            ax1 = fig.add_subplot(2, 4, subplot)
            ax2 = fig.add_subplot(2, 4, subplot + 1)
            subplot += 2
            helper = SharedAxisHelper(ax1, ax2, sharex=sharex, sharey=sharey)
            helpers.append(helper)

    plt.show()
