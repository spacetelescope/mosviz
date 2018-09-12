# This provides a helper class that can be used to link the limits of axes

from glue.utils.matplotlib import defer_draw
from glue.utils.decorators import avoid_circular

__all__ = ['SharedAxisHelper']


def set_xlim_from_ylim(ax):

    position = ax.get_position(original=True)
    fig_width, fig_height = ax.get_figure().get_size_inches()
    fig_aspect = fig_height / fig_width
    l, b, w, h = position.bounds
    box_aspect = fig_aspect * (h / w)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    xmid = 0.5 * (xlim[0] + xlim[1])

    dy = abs(ylim[1] - ylim[0])
    dx = dy / box_aspect

    xlim = xmid - dx / 2., xmid + dx / 2.

    if xlim[1] < xlim[0]:
        xlim = xlim[1], xlim[0]

    ax.set_xlim(*xlim)


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
        # NOTE:  Matplotlib might change ylim back as we have no control over
        # whether it will change xlim or ylim, so to prevent this we change xlim
        # too with set_xlim_from_ylim so that the aspect ratio is correct. This
        # will hopefully be fixed in Matplotlib in future. In the mean time, we
        # apply this 'hack' to ylim only since this is what's needed here for
        # MOSViz. Hopefully, Matplotlib 2.1 will include adjustable='xlim' and
        # adjustable='ylim' options that will mean this workaround is not
        # needed, see https://github.com/matplotlib/matplotlib/pull/8700 for
        # details.
        if self._sharey:
            if axes is self._axes1:
                self._axes2.set_ylim(*self._axes1.get_ylim())
                if (self._axes2.get_adjustable() == 'datalim' and
                    self._axes2.get_aspect() == 'equal'):
                    set_xlim_from_ylim(self._axes2)
                self._axes2.figure.canvas.draw()
            else:
                self._axes1.set_ylim(*self._axes2.get_ylim())
                if (self._axes1.get_adjustable() == 'datalim' and
                    self._axes1.get_aspect() == 'equal'):
                    set_xlim_from_ylim(self._axes1)
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
