# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Utility functions for cutout images."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import os
from functools import partial

# THIRD-PARTY
import numpy as np

# ASTROPY
import astropy.units as u
from astropy import log
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.nddata.utils import Cutout2D
from astropy.table import QTable
from astropy.wcs import WCS, NoConvergence

__all__ = ['make_cutouts', 'show_cutout_with_slit']


def make_cutouts(catalogname, imagename, image_label,
                 table_format='ascii.ecsv', image_ext=0, clobber=False,
                 verbose=True):
    """Make cutouts from a 2D image and write them to FITS files.

    Catalog must have the following columns with unit info, where applicable:

        * ``'id'`` - ID string; no unit necessary.
        * ``'ra'`` - RA (e.g., in degrees).
        * ``'dec'`` - DEC (e.g., in degrees).
        * ``'cutout_x_size'`` - Cutout width (e.g., in arcsec).
        * ``'cutout_y_size'`` - Cutout height (e.g., in arcsec).
        * ``'spatial_pixel_scale'`` - Pixel scale (e.g., in arcsec/pix).

    The following are no longer used, so they are now optional:

        * ``'slit_pa'`` - Slit angle (e.g., in degrees).
        * ``'slit_width'`` - Slit width (e.g., in arcsec).
        * ``'slit_length'`` - Slit length (e.g., in arcsec).

    Cutouts are organized as follows::

        working_dir/
            <image_label>_cutouts/
                <id>_<image_label>_cutout.fits

    Each cutout image is a simple single-extension FITS with updated WCS.
    Its header has the following special keywords:

        * ``OBJ_RA`` - RA of the cutout object in degrees.
        * ``OBJ_DEC`` - DEC of the cutout object in degrees.

    Parameters
    ----------
    catalogname : str
        Catalog table defining the sources to cut out.

    imagename : str
        Image to cut.

    image_label : str
        Label to name the cutout sub-directory and filenames.

    table_format : str, optional
        Format as accepted by `~astropy.table.QTable`. Default is ECSV.

    image_ext : int, optional
        Image extension to extract header and data. Default is 0.

    clobber : bool, optional
        Overwrite existing files. Default is `False`.

    verbose : bool, optional
        Print extra info. Default is `True`.

    """
    table = QTable.read(catalogname, format=table_format)

    with fits.open(imagename) as pf:
        data = pf[image_ext].data
        wcs = WCS(pf[image_ext].header)

    # It is more efficient to operate on an entire column at once.
    c = SkyCoord(table['ra'], table['dec'])
    x = table['cutout_x_size'] / table['spatial_pixel_scale']
    y = table['cutout_y_size'] / table['spatial_pixel_scale']

    # Sub-directory, relative to working directory.
    path = '{0}_cutouts'.format(image_label)
    if not os.path.exists(path):
        os.mkdir(path)

    cutcls = partial(Cutout2D, data, wcs=wcs, mode='partial')

    for position, x_pix, y_pix, row in zip(c, x, y, table):
        try:
            cutout = cutcls(position, size=(y_pix, x_pix))
        except NoConvergence:
            if verbose:
                log.info('WCS solution did not converge: '
                         'Skipping {0}'.format(row['id']))
            continue

        if np.array_equiv(cutout.data, 0):
            if verbose:
                log.info('No data in cutout: Skipping {0}'.format(row['id']))
            continue

        fname = os.path.join(
            path, '{0}_{1}_cutout.fits'.format(row['id'], image_label))

        # Construct FITS HDU.
        hdu = fits.PrimaryHDU(cutout.data)
        hdu.header.update(cutout.wcs.to_header())
        hdu.header['OBJ_RA'] = (position.ra.deg, 'Cutout object RA in deg')
        hdu.header['OBJ_DEC'] = (position.dec.deg, 'Cutout object DEC in deg')

        hdu.writeto(fname, clobber=clobber)

        if verbose:
            log.info('Wrote {0}'.format(fname))


def show_cutout_with_slit(hdr, data=None, slit_ra=None, slit_dec=None,
                          slit_shape='rectangular', slit_width=0.2,
                          slit_length=3.3, slit_angle=90, slit_radius=0.2,
                          slit_rout=0.5, cmap='Greys_r', plotname='',
                          **kwargs):
    """Show a cutout image with the slit(s) superimposed.

    Parameters
    ----------
    hdr : dict
        Cutout image header.

    data : ndarray or `None`, optional
        Cutout image data. If not given, data is not shown.

    slit_ra, slit_dec : float or array or `None`, optional
        Slit RA and DEC in degrees. Default is to use object position
        from image header. If an array is given, each pair of RA and
        DEC becomes a slit.

    slit_shape : {'annulus', 'circular', 'rectangular'}, optional
        Shape of the slit (circular or rectangular).
        Default is rectangular.

    slit_width, slit_length : float, optional
        Rectangular slit width and length in arcseconds.
        Defaults are some fudge values.

    slit_angle : float, optional
        Rectangular slit angle in degrees for the display.
        Default is vertical.

    slit_radius : float, optional
        Radius of a circular or annulus slit in arcseconds.
        For annulus, this is the inner radius.
        Default is some fudge value.

    slit_rout : float, optional
        Outer radius of an annulus slit in arcseconds.
        Default is some fudge value.

    cmap : str or obj, optional
        Matplotlib color map for image display. Default is grayscale.

    plotname : str, optional
        Filename to save plot as. If not given, it is not saved.

    kwargs : dict, optional
        Keyword argument(s) for the aperture overlay.
        If ``ax`` is given, it will also be used for image display.

    See Also
    --------
    make_cutouts

    """
    # Optional dependencies...
    import matplotlib.pyplot as plt
    from photutils import (SkyCircularAnnulus, SkyCircularAperture,
                           SkyRectangularAperture)
    from scipy.ndimage.interpolation import rotate

    if slit_ra is None:
        slit_ra = hdr['OBJ_RA']
    if slit_dec is None:
        slit_dec = hdr['OBJ_DEC']

    position = SkyCoord(slit_ra, slit_dec, unit='deg')

    if slit_shape == 'circular':
        slit_radius = u.Quantity(slit_radius, u.arcsec)
        aper = SkyCircularAperture(position, slit_radius)

    elif slit_shape == 'annulus':
        slit_rin = u.Quantity(slit_radius, u.arcsec)
        slit_rout = u.Quantity(slit_rout, u.arcsec)
        aper = SkyCircularAnnulus(position, slit_rin, slit_rout)

    else:  # rectangular
        slit_width = u.Quantity(slit_width, u.arcsec)
        slit_length = u.Quantity(slit_length, u.arcsec)
        theta = u.Quantity(90, u.degree)
        aper = SkyRectangularAperture(position, slit_width, slit_length,
                                      theta=theta)

        # Rotate data and keep slit upright
        if data is not None:
            data = rotate(data, slit_angle - theta.value, reshape=False)

    wcs = WCS(hdr)
    aper_pix = aper.to_pixel(wcs)
    ax = kwargs.get('ax', plt)

    if data is not None:
        ax.imshow(data, cmap=cmap, origin='lower')

    aper_pix.plot(**kwargs)

    if plotname:
        ax.savefig(plotname)
