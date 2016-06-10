# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Utility functions for MOSViz."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import os
from functools import partial

# THIRD-PARTY
import matplotlib.pyplot as plt

# ASTROPY
import astropy.units as u
from astropy import log
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.nddata.utils import Cutout2D
from astropy.table import QTable
from astropy.wcs import WCS
from photutils import SkyRectangularAperture

__all__ = ['make_cutouts', 'show_cutout_with_slit']


# TODO: Use slit_pa info?
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
        * ``'slit_pa'`` - Slit angle (e.g., in degrees); NOT USED.
        * ``'slit_width'`` - Slit width (e.g., in arcsec).
        * ``'slit_length'`` - Slit length (e.g., in arcsec).

    Cutouts are organized as follows::

        working_dir/
            <image_label>_cutouts/
                <id>_<image_label>_cutout.fits

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
    sw = table['slit_width'].to('arcsec').value
    sl = table['slit_length'].to('arcsec').value

    # Sub-directory, relative to working directory.
    path = '{0}_cutouts'.format(image_label)
    if not os.path.exists(path):
        os.mkdir(path)

    cutcls = partial(Cutout2D, data, wcs=wcs, mode='partial')

    for position, x_pix, y_pix, slit_width, slit_length, row in \
            zip(c, x, y, sw, sl, table):
        cutout = cutcls(position, size=(y_pix, x_pix))
        fname = os.path.join(
            path, '{0}_{1}_cutout.fits'.format(row['id'], image_label))

        # Construct FITS HDU.
        hdu = fits.PrimaryHDU(cutout.data)
        hdu.header.update(cutout.wcs.to_header())
        hdu.header['OBJ_RA'] = (position.ra.deg, 'Cutout object RA in deg')
        hdu.header['OBJ_DEC'] = (position.dec.deg, 'Cutout object DEC in deg')
        hdu.header['SLIT_W'] = (slit_width, 'Slit width in arcsec')
        hdu.header['SLIT_L'] = (slit_length, 'Slit length in arcsec')

        hdu.writeto(fname, clobber=clobber)

        if verbose:
            log.info('Wrote {0}'.format(fname))


# TODO: Replace slit_angle with slit_pa from make_cutouts?
def show_cutout_with_slit(image_label, obj_id, slit_angle=90, cmap='Greys_r',
                          plotname='', **kwargs):
    """Show cutout images with the slit superimposed.

    Parameters
    ----------
    image_label : str
        Label used to name the cutout sub-directory and filenames.

    obj_id : str
        Cutout image ID.

    slit_angle : float, optional
        Slit angle in degrees for the display. Default is vertical.

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
    path = '{0}_cutouts'.format(image_label)
    cutout_fname = os.path.join(
        path, '{0}_{1}_cutout.fits'.format(obj_id, image_label))

    with fits.open(cutout_fname) as pf:
        data = pf[0].data
        hdr = pf[0].header

    # Extract cutout info from header.
    wcs = WCS(hdr)
    position = SkyCoord(hdr['OBJ_RA'], hdr['OBJ_DEC'], unit='deg')
    slit_width = u.Quantity(hdr['SLIT_W'], u.arcsec)
    slit_length = u.Quantity(hdr['SLIT_L'], u.arcsec)
    slit_angle = u.Quantity(slit_angle, u.deg)

    # Contruct slit aperture.
    aper = SkyRectangularAperture(
        position, slit_width, slit_length, theta=slit_angle)
    aper_pix = aper.to_pixel(wcs)

    ax = kwargs.get('ax', plt)

    # Plot the aperture.
    ax.imshow(data, cmap=cmap)
    aper_pix.plot(**kwargs)

    if plotname:
        ax.savefig(plotname)
