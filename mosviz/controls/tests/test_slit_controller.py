import pytest

import numpy as np

from astropy.wcs import WCS
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import proj_plane_pixel_area

from mosviz.viewers.mos_viewer import MOSVizViewer


def construct_test_wcs(ra=0., dec=0., x=0., y=0., area=1.0):
    """
    Constructs an `~astropy.wcs.WCS` object according to params.
    WCS object will always have ['RA---TAN', 'DEC--TAN'] transform.

    Parameters
    ----------
    ra, dec : float
        Center (ra, dec) in deg
    x, y : float
        Center (x, y) pixell
    area : float
        ﻿Projected plane pixel area (deg**2/pix)

    Returns
    --------
    wcs : `~astropy.wcs.WCS`
    """
    axis_scale = np.sqrt(area)
    w = WCS()
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [x, y]
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    w.wcs.cdelt = np.array([-axis_scale, axis_scale])
    return w


def check_is_close(a, b, name_a='a', name_b='b'):
    """
    Parameters
    ----------
    a, b : numeric
        Values to be compared.
    name_a, name_b: str
        Variable name of values.
        Displayed if exception is raised.

    Raises
    ------
    Exception: If a and b and not close
    """
    if not np.isclose(a, b):
        raise Exception("{0} and {1} alues are not close: "
                        "np.isclose({0}, {1})".format(name_a, name_b, a, b))


def check_all_close(a, b, name_a='a', name_b='b'):
    """
    Parameters
    ----------
    a, b : array
        arrays to be compared.
    name_a, name_b : str
        Variable name of arrays.
        Displayed if exception is raised.

    Raises
    ------
    Exception: If values in a and b and not close
    """
    if not np.allclose(a, b):
        raise Exception("{0} and {1} alues are not close: "
                        "np.isclose({0}, {1})".format(name_a, name_b, a, b))


def check_rectangle_patch_attr(slit, x, y, width, length):
    """
    Chcek the patch position, dimension and bounds.
    Params are the expected values.
    Parameters
    ----------
    slit : _MOSVizSlit
        Slit to be tested.
    x, y, width, length : float
        Correct center x pixel, center y pixel, width and length.
    """

    x_bounds = np.array([x - (width / 2.), x + (width / 2.)])
    y_bounds = np.array([y - (length / 2.), y + (length / 2.)])

    check_is_close(slit.x, x)
    check_is_close(slit.y, y)
    check_is_close(slit.dx, width)
    check_is_close(slit.dy, length)
    check_is_close(slit.width, width)
    check_is_close(slit.length, length)
    check_all_close(np.array(slit.x_bounds), x_bounds)
    check_all_close(np.array(slit.y_bounds), y_bounds)
    check_all_close(np.array(slit.y_bounds), y_bounds)


def check_clear_slits(slit_controller):
    """Make sure all attributes are reset"""
    assert slit_controller.has_slits is False
    assert len(slit_controller.slits) == 0


def test_construct_pix_region(glue_gui):
    """Test the `SlitController.construct_pix_region` function"""
    mosviz_gui = MOSVizViewer(glue_gui.session)
    slit_controller = mosviz_gui.slit_controller

    # Construct a 20x10 (l x w) rectangle
    x, y = (5., 10.)
    width = 10.
    length = 20.

    assert not slit_controller.has_slits
    slit_controller.add_rectangle_pixel_slit(x=x, y=y, width=width, length=length)
    assert slit_controller.has_slits

    check_rectangle_patch_attr(slit_controller.slits[0], x, y, width, length)

    # Test move function for this parch
    x, y = (500., 100.)
    slit_controller.slits[0].move(x=x, y=y)

    check_rectangle_patch_attr(slit_controller.slits[0], x, y, width, length)

    # Test drawing the slit
    mosviz_gui.image_widget.draw_slit()

    # Test removing the paths
    slit_controller.clear_slits()
    check_clear_slits(slit_controller)
    mosviz_gui.close(warn=False)


def test_construct_sky_region(glue_gui):
    """Test the `SlitController.construct_sky_region` function"""
    mosviz_gui = MOSVizViewer(glue_gui.session)
    slit_controller = mosviz_gui.slit_controller

    ra, dec = (10., 30.)
    x, y = (5., 10.)
    ang_width = 1.  # deg
    ang_length = 2.  # deg
    area = 0.1  # deg**2/pix
    scale = np.sqrt(area)
    width = ang_width / scale
    length = ang_length / scale

    # note fits indexing starts at 1
    wcs = construct_test_wcs(ra, dec, x+1, y+1, area)

    assert not slit_controller.has_slits
    slit_controller.add_rectangle_sky_slit(wcs, ra, dec,
                                           (ang_width*u.deg).to(u.arcsec),
                                           (ang_length*u.deg).to(u.arcsec))
    assert slit_controller.has_slits

    check_rectangle_patch_attr(slit_controller.slits[0], x, y, width, length)

    # Test move function for this parch
    x, y = (500., 100.)
    slit_controller.slits[0].move(x=x, y=y)

    check_rectangle_patch_attr(slit_controller.slits[0], x, y, width, length)

    # Test drawing the slit
    mosviz_gui.image_widget.draw_slit()

    # Test removing the paths
    slit_controller.clear_slits()
    check_clear_slits(slit_controller)
    mosviz_gui.close(warn=False)


def test_launch_editor(glue_gui):
    """Test launching the slit editor"""
    mosviz_gui = MOSVizViewer(glue_gui.session)
    slit_controller = mosviz_gui.slit_controller
    ui = slit_controller.launch_slit_ui()
    mosviz_gui.close(warn=False)

    mosviz_gui = glue_gui.viewers[0][0]
    slit_controller = mosviz_gui.slit_controller
    ui = slit_controller.launch_slit_ui()
    ui.close()


def test_current_slit(glue_gui):
    """Test the UI currently available for testing."""
    mosviz_gui = glue_gui.viewers[0][0]
    slit_controller = mosviz_gui.slit_controller

    if "slit_width" in mosviz_gui.catalog.meta["special_columns"] and \
            "slit_length" in mosviz_gui.catalog.meta["special_columns"] and \
            mosviz_gui.cutout_wcs is not None:
        assert slit_controller.has_slits
        row = mosviz_gui.current_row
        ra = row[mosviz_gui.catalog.meta["special_columns"]["slit_ra"]]
        dec = row[mosviz_gui.catalog.meta["special_columns"]["slit_dec"]]
        ang_width = row[mosviz_gui.catalog.meta["special_columns"]["slit_width"]]
        ang_length = row[mosviz_gui.catalog.meta["special_columns"]["slit_length"]]

        wcs = mosviz_gui.cutout_wcs

        skycoord = SkyCoord(ra, dec, frame='fk5', unit="deg")
        xp, yp = skycoord.to_pixel(wcs)

        scale = np.sqrt(proj_plane_pixel_area(wcs)) * 3600.

        dx = ang_width / scale
        dy = ang_length / scale

        check_is_close(dx, slit_controller.slits[0].dx)
        check_is_close(dy, slit_controller.slits[0].dy)
        check_is_close(xp, slit_controller.slits[0].x)
        check_is_close(yp, slit_controller.slits[0].y)
