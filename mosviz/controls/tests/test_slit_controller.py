import pytest

import numpy as np

from astropy.wcs import WCS
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import proj_plane_pixel_area

from mosviz.viewers.mos_viewer import MOSVizViewer


def construct_test_wcs(ra=0., dec=0., x=0.0, y=0.0, area=1.0):
    """
    Constructs an `~astropy.wcs.WCS` object according to params.
    WCS object will always have ['RA---TAN', 'DEC--TAN'] transform.
    :param ra: Center RA in deg
    :param dec: Center DEC in deg
    :param x: Center x pixel
    :param y: Center Y pixel
    :param area: ﻿Projected plane pixel area (deg**2/pix)
    :return: `~astropy.wcs.WCS`
    """
    axis_scale = np.sqrt(area)
    w = WCS()
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [x, y]
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    w.wcs.cdelt = np.array([axis_scale, axis_scale])
    return w


def check_slits_and_patchs(slit_controller):
    """Check if patch is correctly available"""
    assert slit_controller.is_active == (slit_controller._patch is not None)

    if slit_controller._pix_slit is not None and slit_controller._patch is None:
        raise Exception("Slit Controller has _pix_slit but no patch.")
    if slit_controller._slit is not None and slit_controller._patch is None:
        raise Exception("Slit Controller has _slit but no patch.")

    patch = slit_controller.patch
    assert(patch is not None) == slit_controller.is_active


def check_patch_attr(slit_controller, x, y, width, length):
    """
    Chcek the patch position, dimension and bounds.
    Params are the expected values.
    :param slit_controller: SlitController
    :param x: correct center x pixel
    :param y: correct center y pixel
    :param width: correct width
    :param length: correct length
    """

    x_bounds = np.array([x - (width / 2.), x + (width / 2.)])
    y_bounds = np.array([y - (length / 2.), y + (length / 2.)])

    assert np.isclose(slit_controller.x, x)
    assert np.isclose(slit_controller.y, y)
    assert np.isclose(slit_controller.dx, width)
    assert np.isclose(slit_controller.dy, length)
    assert np.isclose(slit_controller.width, width)
    assert np.isclose(slit_controller.length, length)
    assert np.allclose(np.array(slit_controller.x_bounds), x_bounds)
    assert np.allclose(np.array(slit_controller.y_bounds), y_bounds)


def check_distruction(slit_controller):
    """Make sure all attributes are reset"""
    assert slit_controller.is_active is False
    assert slit_controller._patch is None
    assert slit_controller._slit is None
    assert slit_controller._pix_slit is None


def test_construct_simple_rectangle(glue_gui):
    """Test the `SlitController.construct_simple_rectangle` function"""
    mosviz_gui = MOSVizViewer(glue_gui.session)
    slit_controller = mosviz_gui.slit_controller

    # Construct a 20x10 (l x w) rectangle
    x, y = (5., 10.)
    width = 10.
    length = 20.

    slit_controller.construct_simple_rectangle(x=x, y=y, width=width, length=length)

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test move function for this parch
    x, y = (500., 100.)
    slit_controller.move(x=x, y=y)

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test drawing the slit
    mosviz_gui.image_widget.draw_slit()

    # Test removing the path
    slit_controller.destruct()
    check_distruction(slit_controller)

    mosviz_gui.close(warn=False)


def test_construct_pix_region(glue_gui):
    """Test the `SlitController.construct_pix_region` function"""
    mosviz_gui = MOSVizViewer(glue_gui.session)
    slit_controller = mosviz_gui.slit_controller

    # Construct a 20x10 (l x w) rectangle
    x, y = (5., 10.)
    width = 10.
    length = 20.

    slit_controller.construct_pix_region(x=x, y=y, width=width, length=length)

    assert slit_controller._pix_slit is not None

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test move function for this parch
    x, y = (500., 100.)
    slit_controller.move(x=x, y=y)

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test drawing the slit
    mosviz_gui.image_widget.draw_slit()

    # Test removing the path
    slit_controller.destruct()
    check_distruction(slit_controller)
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

    slit_controller.construct_sky_region(wcs, ra, dec,
                                         (ang_width*u.deg).to(u.arcsec),
                                         (ang_length*u.deg).to(u.arcsec))

    assert slit_controller._slit is not None
    assert slit_controller._pix_slit is not None

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test move function for this parch
    x, y = (500., 100.)
    slit_controller.move(x=x, y=y)

    check_slits_and_patchs(slit_controller)
    check_patch_attr(slit_controller, x, y, width, length)

    # Test drawing the slit
    mosviz_gui.image_widget.draw_slit()

    # Test removing the path
    slit_controller.destruct()
    check_distruction(slit_controller)
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
        mosviz_gui.render
        assert slit_controller.is_active
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

        assert np.isclose(dx, slit_controller.dx)
        assert np.isclose(dy, slit_controller.dy)
        assert np.isclose(xp, slit_controller.x)
        assert np.isclose(yp, slit_controller.y)
