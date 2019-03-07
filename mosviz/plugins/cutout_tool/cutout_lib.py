import os
import errno
import math

import numpy as np
from functools import partial

from astropy.table import Table, QTable
import astropy.units as u
from astropy.io import fits
from astropy.io.fits import PrimaryHDU, ImageHDU, CompImageHDU
from astropy.wcs import WCS, NoConvergence
from astropy.wcs.utils import wcs_to_celestial_frame, proj_plane_pixel_scales
from astropy.coordinates import SkyCoord
from astropy.nddata import NDData
from astropy.nddata.utils import (Cutout2D, NoOverlapError)
from astropy import log



# These two functions should be replaced by
# imports from astropy.nddata.utils


def make_cutouts(data, catalog, wcs=None, origin=0, verbose=True):
    """Make cutouts of catalog targets from a 2D image array.
    Expects input image WCS to be in the TAN projection.

    Parameters
    ----------
    data : 2D `~numpy.ndarray` or `~astropy.nddata.NDData`
        The 2D cutout array.
    catalog : `~astropy.table.table.Table`
        Catalog table defining the sources to cut out. Must contain
        unit information as the cutout tool does not assume default units.
    wcs : `~astropy.wcs.wcs.WCS`
        WCS if the input image is `~numpy.ndarray`.
    origin : int
        Whether SkyCoord.from_pixel should use 0 or 1-based pixel coordinates.
    verbose : bool
        Print extra info. Default is `True`.

    Returns
    -------
    cutouts : list
        A list of NDData. If cutout failed for a target,
       `None` will be added as a place holder. Output WCS
       will in be in Tan projection.

    Notes
    -----
    The input Catalog must have the following columns, which MUST have
    units information where applicable:

        * ``'id'`` - ID string; no unit necessary.
        * ``'coords'`` - SkyCoord (Overrides ra, dec, x and y columns).
        * ``'ra'`` or ``'x'``- RA (angular units e.g., deg, H:M:S, arcsec etc..)
          or pixel x position (only in `~astropy.units.pix`).
        * ``'dec'`` or ``'y'`` - Dec (angular units e.g., deg, D:M:S, arcsec etc..)
          or pixel y position (only in `~astropy.units.pix`).
        * ``'cutout_width'`` - Cutout width (e.g., in arcsec, pix).
        * ``'cutout_height'`` - Cutout height (e.g., in arcsec, pix).

    Optional columns:
        * ``'cutout_pa'`` - Cutout angle (e.g., in deg, arcsec). This is only
          use if user chooses to rotate the cutouts. Positive value
          will result in a clockwise rotation.

    If saved to fits, cutouts are organized as follows:
        <output_dir>/
            <id>.fits

    Each cutout image is a simple single-extension FITS with updated WCS.
    Its header has the following special keywords:

        * ``OBJ_RA`` - RA of the cutout object in degrees.
        * ``OBJ_DEC`` - DEC of the cutout object in degrees.
        * ``OBJ_ROT`` - Rotation of cutout object in degrees.

    """
    # Do not rotate if column is missing.
    if 'cutout_pa' in catalog.colnames:
        if catalog['cutout_pa'].unit is None:
            raise u.UnitsError("Units not specified for cutout_pa.")
        apply_rotation = True
    else:
        apply_rotation = False

    # Optional dependencies...
    if apply_rotation:
        try:
            from reproject.interpolation.high_level import reproject_interp
        except ImportError as e:
            raise ImportError("Optional requirement not met: " + e.msg)

    # Search for wcs:
    if isinstance(data, NDData):
            if wcs is not None:
                raise Exception("Ambiguous: WCS defined in NDData and parameters.")
            wcs = data.wcs
    elif not isinstance(data, np.ndarray):
        raise TypeError("Input image should be a 2D `~numpy.ndarray` "
                        "or `~astropy.nddata.NDData")
    elif wcs is None:
        raise Exception("WCS information was not provided.")

    if wcs.wcs.ctype[0] != 'RA---TAN' or  wcs.wcs.ctype[1] != 'DEC--TAN':
        raise Exception("Expected  WCS to be in the TAN projection.")

    # Calculate the pixel scale of input image:
    pixel_scales = proj_plane_pixel_scales(wcs)
    pixel_scale_width = pixel_scales[0] * u.Unit(wcs.wcs.cunit[0]) / u.pix
    pixel_scale_height = pixel_scales[1] * u.Unit(wcs.wcs.cunit[1]) / u.pix

    # Check if `SkyCoord`s are available:
    if 'coords' in catalog.colnames:
        coords = catalog['coords']
        if not isinstance(coords, SkyCoord):
            raise TypeError('The coords column is not a SkyCoord')
    elif 'ra' in catalog.colnames and 'dec' in catalog.colnames:
        if 'x' in catalog.colnames and 'y' in catalog.colnames:
            raise Exception("Ambiguous catalog: Both (ra, dec) and pixel positions provided.")
        if catalog['ra'].unit is None or catalog['dec'].unit is None:
            raise u.UnitsError("Units not specified for ra and/or dec columns.")
        coords = SkyCoord(catalog['ra'], catalog['dec'], unit=(catalog['ra'].unit,
                                                               catalog['dec'].unit))
    elif 'x' in catalog.colnames and 'y' in catalog.colnames:
        coords = SkyCoord.from_pixel(catalog['x'].astype(float), catalog['y'].astype(float), wcs, origin=origin)
    else:
        try:
            coords = SkyCoord.guess_from_table(catalog)
        except Exception as e:
            raise e

    coords = coords.transform_to(wcs_to_celestial_frame(wcs))

    # Figure out cutout size:
    if 'cutout_width' in catalog.colnames:
        if catalog['cutout_width'].unit is None:
            raise u.UnitsError("Units not specified for cutout_width.")
        if catalog['cutout_width'].unit == u.pix:
            width = catalog['cutout_width'].astype(float)  # pix
        else:
            width = (catalog['cutout_width'] / pixel_scale_width).decompose().value  # pix
    else:
        raise Exception("cutout_width column not found in catalog.")

    if 'cutout_height' in catalog.colnames:
        if catalog['cutout_height'].unit is None:
            raise u.UnitsError("Units not specified for cutout_height.")
        if catalog['cutout_height'].unit == u.pix:
            height = catalog['cutout_height'].astype(float)  # pix
        else:
            height = (catalog['cutout_height'] / pixel_scale_height).decompose().value  # pix
    else:
        raise Exception("cutout_height column not found in catalog.")

    cutcls = partial(Cutout2D, data.data, wcs=wcs, mode='partial')
    cutouts = []
    for position, x_pix, y_pix, row in zip(coords, width, height, catalog):

        if apply_rotation:
            pix_rot = row['cutout_pa'].to(u.degree).value

            # Construct new rotated WCS:
            cutout_wcs = WCS(naxis=2)
            cutout_wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
            cutout_wcs.wcs.crval = [position.ra.deg, position.dec.deg]
            cutout_wcs.wcs.crpix = [(x_pix + 1) * 0.5, (y_pix + 1) * 0.5]

            try:
                cutout_wcs.wcs.cd = wcs.wcs.cd
                cutout_wcs.rotateCD(-pix_rot)
            except AttributeError:
                cutout_wcs.wcs.cdelt = wcs.wcs.cdelt
                cutout_wcs.wcs.crota = [0, -pix_rot]

            cutout_hdr = cutout_wcs.to_header()

            # Rotate the image using reproject
            try:
                cutout_arr = reproject_interp(
                    (data, wcs), cutout_hdr, shape_out=(math.floor(y_pix + math.copysign(0.5, y_pix)),
                                                        math.floor(x_pix + math.copysign(0.5, x_pix))), order=1)
            except Exception:
                if verbose:
                    log.info('reproject failed: '
                             'Skipping {0}'.format(row['id']))
                cutouts.append(None)
                continue

            cutout_arr = cutout_arr[0]  # Ignore footprint
            cutout_hdr['OBJ_ROT'] = (pix_rot, 'Cutout rotation in degrees')
        else:
            # Make cutout or handle exceptions by adding None to output list
            try:
                cutout = cutcls(position, size=(y_pix, x_pix))
            except NoConvergence:
                if verbose:
                    log.info('WCS solution did not converge: '
                             'Skipping {0}'.format(row['id']))
                cutouts.append(None)
                continue
            except NoOverlapError:
                if verbose:
                    log.info('Cutout is not on image: '
                             'Skipping {0}'.format(row['id']))
                cutouts.append(None)
                continue
            else:
                cutout_hdr = cutout.wcs.to_header()
                cutout_arr = cutout.data

        # If cutout result is empty, skip that target
        if np.array_equiv(cutout_arr, 0):
            if verbose:
                log.info('No data in cutout: Skipping {0}'.format(row['id']))
            cutouts.append(None)
            continue

        # Finish constructing header.
        cutout_hdr['OBJ_RA'] = (position.ra.deg, 'Cutout object RA in deg')
        cutout_hdr['OBJ_DEC'] = (position.dec.deg, 'Cutout object DEC in deg')

        cutouts.append(NDData(data=cutout_arr, wcs=WCS(cutout_hdr), meta=cutout_hdr))

    return cutouts


def cutouts_from_fits(image, catalog, image_ext=0, origin=0,
                      output_dir=None, overwrite=False, verbose=True):
    """Wrapper for the make_cutouts function. This function will take in a single
    fits image and return an array containing a list of cutouts as fits hdus. It
    will also save the cutouts to file if requested.
    Expects input image WCS to be in the TAN projection.

    Parameters
    ----------
    image : filename or `HDUList` or `PrimaryHDU` or `ImageHDU` or `CompImageHDU`
        Image to cut from. If string is provided, it is assumed to be a
        fits file path.
    catalog : str or `~astropy.table.table.Table`
        Catalog table defining the sources to cut out. Must contain
        unit information as the cutout tool does not assume default units.
        Must be an astropy Table or a file name to an ECSV file containing sources.
    image_ext : int, optional
        If image is in an HDUList or read from file, use this image extension index
        to extract header and data from the primary image. Default is 0.
    origin : int
        Whether SkyCoord.from_pixel should use 0 or 1-based pixel coordinates.
    output_dir : str
        Path to directory to save the cutouts in. If provided, each cutout will be
        saved to a separate file. The directory is created if it does not exist.
    overwrite: bool, optional
        Overwrite existing files. Default is `False`.
    verbose : bool, optional
        Print extra info. Default is `True`.

    Returns
    -------
    cutouts : list
        A list of NDData or fits PrimaryHDU. If cutout failed for a target,
       `None` will be added as a place holder. Output WCS
       will in be in Tan projection.

    Notes
    -----
    The input Catalog must have the following columns, which MUST have
    units information where applicable:

        * ``'id'`` - ID string; no unit necessary.
        * ``'coords'`` - SkyCoord (Overrides ra, dec, x and y columns).
        * ``'ra'`` or ``'x'``- RA (angular units e.g., deg, H:M:S, arcsec etc..)
          or pixel x position (only in `~astropy.units.pix`).
        * ``'dec'`` or ``'y'`` - Dec (angular units e.g., deg, D:M:S, arcsec etc..)
          or pixel y position (only in `~astropy.units.pix`).
        * ``'cutout_width'`` - Cutout width (e.g., in arcsec, pix).
        * ``'cutout_height'`` - Cutout height (e.g., in arcsec, pix).

    Optional columns:
        * ``'cutout_pa'`` - Cutout angle (e.g., in deg, arcsec). This is only
          use if user chooses to rotate the cutouts. Positive value
          will result in a clockwise rotation.

    If saved to fits, cutouts are organized as follows:
        <output_dir>/
            <id>.fits

    Each cutout image is a simple single-extension FITS with updated WCS.
    Its header has the following special keywords:

        * ``OBJ_RA`` - RA of the cutout object in degrees.
        * ``OBJ_DEC`` - DEC of the cutout object in degrees.
        * ``OBJ_ROT`` - Rotation of cutout object in degrees.

    Examples
    --------
    Given a list of Hubble Ultra Deep Field RA and Dec coords,
    you may use the tool as follows:
        # >>> from astropy.table import Table
        # >>> import astropy.units as u
        #
        # >>> ra = [53.18782913, 53.14794797, 53.15059559] * u.deg
        # >>> dec = [-27.79405589, -27.77392421, -27.77158621] * u.deg
        # >>> ids = ["Galax_0", 123, 53.15059559 * u.deg]
        # >>> cutout_width = cutout_height = [3.0, 4.0, 3.0] * u.arcsec
        #
        # >>> catalog = Table(
        # ...     data=[ids, ra, dec, cutout_width, cutout_height],
        # ...     names=['id', 'ra', 'dec', 'cutout_width', 'cutout_height'])
        #
        # # To get a list of PrimaryHDU objects:
        # >>> cutouts = cutouts_from_fits('h_udf_wfc_b_drz_img.fits', catalog)
        # # To save to fits file provide an output dir:
        # >>> cutouts = cutouts_from_fits('h_udf_wfc_b_drz_img.fits', catalog, output_dir='~/cutouts')
        #
        # # The input image can be read in before the function call:
        # >>> image = fits.open('h_udf_wfc_b_drz_img.fits')
        # >>> cutouts = cutouts_from_fits(image, catalog, image_ext=0)
        #
        # # If the above catalog table is saved in an ECSV file with the proper units information:
        # >>> catalog.write('catalog.ecsv', format='ascii.ecsv')
        # >>> cutouts = cutouts_from_fits('h_udf_wfc_b_drz_img.fits', 'catalog.ecsv')
    """
    save_to_file = output_dir is not None

    # read in the catalog file:
    if isinstance(catalog, str):
        catalog = QTable.read(catalog)
    elif not isinstance(catalog, Table):
        raise TypeError("Catalog should be an astropy.table.table.Table or"
                        " file name, got {0} instead".format(type(catalog)))

    # Load data and wcs:
    if isinstance(image, str):
        # Read data and WCS from file
        with fits.open(image) as pf:
            image_hdu = pf[image_ext]
            data = image_hdu.data
            wcs = WCS(image_hdu.header)
    else:
        # If image is HDUList or HDU:
        if isinstance(image, fits.hdu.hdulist.HDUList):
            image_hdu = image[image_ext]
        elif isinstance(image, (PrimaryHDU, ImageHDU, CompImageHDU)):
            image_hdu = image
        else:
            raise TypeError("Expected array, ImageHDU, HDUList, or file "
                            "name. Got {0} instead".format(type(image)))
        data = image_hdu.data
        wcs = WCS(image_hdu.header)

    # If image is empty, raise exception
    if np.array_equiv(data, 0):
        raise ValueError("No data in image.")

    # Sub-directory, relative to working directory.
    if save_to_file:
        path = output_dir
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass

    # Make the cutouts using the make_cutouts function:
    cutouts = make_cutouts(data=data, catalog=catalog, wcs=wcs,
                           origin=origin, verbose=verbose)

    # Convert cutouts to fits hdus.
    # Save the hdus to file if requested:
    fits_cutouts = []
    for idx, cutout in enumerate(cutouts):
        if cutout is None:
            fits_cutouts.append(None)
            continue

        row = catalog[idx]
        cutout_arr = cutout.data
        cutout_hdr = cutout.meta

        # Construct FITS HDU.
        hdu = fits.PrimaryHDU(cutout_arr)
        hdu.header.update(cutout_hdr)

        # Save to file if output directory is provided
        if save_to_file:
            fname = os.path.join(
                path, '{0}.fits'.format(row['id']))
            try:
                hdu.writeto(fname, overwrite=overwrite)
            except OSError as e:
                if not overwrite:
                    raise OSError(str(e) + " Try setting overwrite parameter to True.")
                else:
                    raise e
            if verbose:
                log.info('Wrote {0}'.format(fname))

        # Add cutout to output list
        fits_cutouts.append(hdu)

    return fits_cutouts
