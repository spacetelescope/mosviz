class _MOSVizSlit:
    """
    Base class for MOSViz Slits.
    The properties and functions are required to
    communicate with the MOSViz widget.
    """
    @property
    def is_active(self):
        raise NotImplementedError("MOSVizSlit.is_active not implemented")

    @property
    def x(self):
        """Center x position of slit"""
        raise NotImplementedError("MOSVizSlit.x not implemented")

    @property
    def y(self):
        """Center y position of slit"""
        raise NotImplementedError("MOSVizSlit.y not implemented")

    @property
    def x_bounds(self):
        """x axis min and max pixel values as tuple(min, max). None if n/a."""
        raise NotImplementedError("MOSVizSlit.x_bounds not implemented")

    @property
    def y_bounds(self):
        """y axis min and max pixel values as tuple(min, max). None if n/a."""
        raise NotImplementedError("MOSVizSlit.y_bounds not implemented")

    def draw(self, ax=None):
        """Draw slit on axes ax"""
        raise NotImplementedError("MOSVizSlit.draw not implemented")

    def move(self, x, y):
        """
        Move the bottom right corner of the patch.

        Parameters
        ----------
        x, y : float
            Center (x, y) of slit in pix.
        """
        raise NotImplementedError("MOSVizSlit.move not implemented")

    def remove(self):
        """Remove the patch from the axes its drawn in."""
        raise NotImplementedError("MOSVizSlit.remove not implemented")
