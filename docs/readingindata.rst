***************
Reading-in Data
***************

MOSViz will be able to read in NIRSpec MSA data straight from the pipeline or archive.
This will include 1D and 2D spectra, images, data tables, and associated images.
This page documents how to read in MOS data from another observatory.
An example is shown at the bottom (:ref:`reading_in_data`).

++++++++
Overview
++++++++

MOSViz requires at minimum the following input:

* data table

* 1D or 2D spectra.

The user can also incorporate:

* cut-out images of targets.

++++++++++
Data Table
++++++++++

The data table is required to contain at minimum:

* target names/numbers

* target RA, DEC

* paths and file names of 1D or 2D spectra.

It can additionally contain:

* paths and file names of cut-out images

* any other quantities the user wishes (e.g., magnitudes, stellar masses, star-formation rates, etc.).

+++++++++++++++++++++++++++++++++++++++++++++++++++++
Required Format and Header Information for 1D Spectra
+++++++++++++++++++++++++++++++++++++++++++++++++++++

+++++++++++++++++++++++++++++++++++++++++++++++++++++
Required Format and Header Information for 2D Spectra
+++++++++++++++++++++++++++++++++++++++++++++++++++++

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Required Format and Header Information for Cut Out Images
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. _reading_in_data:

********************************
Example of Reading-in a Data Set
********************************

This example consists of galaxies at 0.2<z<1.2 which have spectra from the DEIMOS
multi-object spectrograph on Keck and color cut-out images already created from
Hubble/ACS.  These galaxies are from the `DEEP2 Survey <http://adsabs.harvard.edu/abs/2013ApJS..208....5N>`_.

+++++++++++++++++
Glue Data Loaders
+++++++++++++++++

MOSViz is a Glue plugin so we'll write our own `Custom Data Loaders <http://glueviz.org/en/stable/customizing_guide/customization.html#custom-data-loaders>`_ to read data.  All we need to do is write a function which takes a filename as input and returns a glue `Data` object.  For this example, we have three different types of data: a 1D Spectrum, a 2D spectrum, and a cutout image.  The following sections walk through writing data loaders for each of these data type.

++++++++++++++++++
1D Spectrum Reader
++++++++++++++++++

.. code-block:: python

    @data_factory('DEIMOS 1D Spectrum')
    def deimos_spectrum1D_reader(file_name):
        """
        Data loader for Keck/DEIMOS 1D spectra.

        This loads the 'Bxspf-B' (extension 1)
        and 'Bxspf-R' (extension 2) and appends them
        together to proudce the combined Red/Blue Spectrum
        along with their Wavelength and Inverse Variance
        arrays.
        """

        hdulist = fits.open(file_name)
        data = Data(label='1D Spectrum')
        data.header = hdulist[1].header

        full_wl = np.append(hdulist[1].data['LAMBDA'][0], hdulist[2].data['LAMBDA'][0])
        full_spec = np.append(hdulist[1].data['SPEC'][0], hdulist[2].data['SPEC'][0])
        full_ivar = np.append(hdulist[1].data['IVAR'][0], hdulist[2].data['IVAR'][0])

        data.add_component(full_wl, 'Wavelength')
        data.add_component(full_spec, 'Flux')
        data.add_component(full_ivar, 'Uncertainty')

        return data

MOSViz expects the 1D Spectrum Data object to have three components: Wavelength, Flux, and Uncertainty.  
Let's take a look at the contents of our example FITS file to see which parts we need to pass to MOSViz.

.. code-block:: python

    >>> from astropy.io import fits
    >>> hdulist = fits.open('spec1d.1355.134.13040873.fits')
    >>> hdulist.info()
    Filename: spec1d.1355.134.13040873.fits
    No.    Name         Type      Cards   Dimensions   Format
    0    PRIMARY     PrimaryHDU       4   ()
    1    Bxspf-B     BinTableHDU    131   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    2    Bxspf-R     BinTableHDU    131   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    3    Horne-B     BinTableHDU    140   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    4    Horne-R     BinTableHDU    140   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    5    Bxspf-NL-B  BinTableHDU    131   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    6    Bxspf-NL-R  BinTableHDU    131   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    7    Horne-NL-B  BinTableHDU    140   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]
    8    Horne-NL-R  BinTableHDU    140   1R x 15C     [4096E, 4096E, 4096E, 4096I, 4096I, 4096I, 4096I, 4096I, E, E, E, J, J, 4096E, E]

The file contains pairs of red and blue spectra which have been filtered in various ways. 
For the sake of this example we'll choose the `Bxspf` spectra.

Taking a closer look at the relevant extension

.. code-block:: python

    >>> hdulist['Bxspf-R'].columns
    ColDefs(
        name = 'SPEC'; format = '4096E'
        name = 'LAMBDA'; format = '4096E'
        name = 'IVAR'; format = '4096E'
        name = 'CRMASK'; format = '4096I'
        name = 'BITMASK'; format = '4096I'
        name = 'ORMASK'; format = '4096I'
        name = 'NBADPIX'; format = '4096I'
        name = 'INFOMASK'; format = '4096I'
        name = 'OBJPOS'; format = 'E'
        name = 'FWHM'; format = 'E'
        name = 'NSIGMA'; format = 'E'
        name = 'R1'; format = 'J'
        name = 'R2'; format = 'J'
        name = 'SKYSPEC'; format = '4096E'
        name = 'IVARFUDGE'; format = 'E'
    )
    >>> hdulist['Bxspf-B'].columns
    ColDefs(
        name = 'SPEC'; format = '4096E'
        name = 'LAMBDA'; format = '4096E'
        name = 'IVAR'; format = '4096E'
        name = 'CRMASK'; format = '4096I'
        name = 'BITMASK'; format = '4096I'
        name = 'ORMASK'; format = '4096I'
        name = 'NBADPIX'; format = '4096I'
        name = 'INFOMASK'; format = '4096I'
        name = 'OBJPOS'; format = 'E'
        name = 'FWHM'; format = 'E'
        name = 'NSIGMA'; format = 'E'
        name = 'R1'; format = 'J'
        name = 'R2'; format = 'J'
        name = 'SKYSPEC'; format = '4096E'
        name = 'IVARFUDGE'; format = 'E'
    )

Again, there are a lot of options but for MOSViz we're only interested in three columns: `SPEC`, `LAMBDA`, `IVAR`.
Further, MOSViz expects each of the arrays to be 1 dimensional and of the same size.

.. code-block:: python
    
    >>> hdulist['Bxspf-R'].data['SPEC'].shape
    (1, 4096)
    >>> hdulist['Bxspf-R'].data['LAMBDA'].shape
    (1, 4096)
    >>> hdulist['Bxspf-R'].data['IVAR'].shape
    (1, 4096)

All of our arrays are the same size but they are stored in 2 dimensional arrays (with the first axis of size 1). 
So we'll just take the first (and only) element.

Now that we know what data we want from our FITS files let's look at how to write the data loader function.

.. code-block:: python

    @data_factory('DEIMOS 1D Spectrum')

The `@data_factory` decorator tells Glue that this is a function used to load data.

.. code-block:: python
    
    def deimos_spectrum1D_reader(file_name):

The function itself takes a filename to open as its only argument.  
The function name `deimos_spectrum1D_reader` is what will go into the header of catalog file to tell MOSViz how to load 1D spectra.

.. code-block:: python
    
        hdulist = fits.open(file_name)
        data = Data(label='1D Spectrum')

Now as above we're going to open the FITS file.  
Then we instantiate a Glue `Data` object which will be populated with the data we wish to pass to MOSViz.

.. code-block:: python
        
        data.header = hdulist[1].header

MOSViz has an info box which can display metadata so we'll make the FITS header available to the `Data` object.

.. code-block:: python

        full_wl = np.append(hdulist[1].data['LAMBDA'][0], hdulist[2].data['LAMBDA'][0])
        full_spec = np.append(hdulist[1].data['SPEC'][0], hdulist[2].data['SPEC'][0])
        full_ivar = np.append(hdulist[1].data['IVAR'][0], hdulist[2].data['IVAR'][0])

        data.add_component(full_wl, 'Wavelength')
        data.add_component(full_spec, 'Flux')
        data.add_component(full_ivar, 'Uncertainty')

        return data

As stated above, MOSViz expects the Wavelength, Flux, and Uncertainty to be each be a single 1D array.
We saw that the red and blue ends of the spectrum are stored in different extensions and that there are stored as 2D arrays.
We take the first component of the each of the red and blue ends of the spectrum and combine them together.
Then we take the full 1D array for each component and pass them to the `data` object using the `add_component()` method.

++++++++++++++++++
2D Spectrum Reader
++++++++++++++++++

.. code-block:: python

    @data_factory('DEIMOS 2D Spectrum')
    def deimos_spectrum2D_reader(file_name):
        """
        Data loader for Keck/DEIMOS 2D spectra.

        This loads only the Flux and Inverse variance.
        Wavelength information comes from the WCS.
        """

        hdulist = fits.open(file_name)
        data = Data(label='2D Spectrum')
        data.coords = coordinates_from_header(hdulist[1].header)
        data.header = hdulist[1].header
        data.add_component(hdulist[1].data['FLUX'][0], 'Flux')
        data.add_component(hdulist[1].data['IVAR'][0], 'Uncertainty')
        return data

MOSViz expects the 2D Spectrum Data object to have two components: Flux and Uncertainty.
Since a 2D spectrum is an image it also expects a World Coordinate System (WCS) which tells it how to transform from pixels to Wavelength.  
Let's take a look at the contents of our example FITS file to see which parts we need to pass to MOSViz.

.. code-block:: python

    >>> from astropy.io import fits
    >>> hdulist = fits.open('slit.1153.147B.fits.gz')
    >>> hdulist.info()
    Filename: slit.1153.147B.fits.gz
    No.    Name         Type      Cards   Dimensions   Format
    0    PRIMARY     PrimaryHDU       4   ()
    1    slit        BinTableHDU    106   1R x 11C     [241664E, 241664E, 241664B, 241664B, 4096E, 241664E, 6D, 3D, 59E, 177E, 241664J]
    2    slit        BinTableHDU     98   531R x 5C    [E, E, E, E, B]
    >>> hdulist[1].data.columns
    ColDefs(
        name = 'FLUX'; format = '241664E'; dim = '( 4096, 59)'
        name = 'IVAR'; format = '241664E'; dim = '( 4096, 59)'
        name = 'MASK'; format = '241664B'; dim = '( 4096, 59)'
        name = 'CRMASK'; format = '241664B'; dim = '( 4096, 59)'
        name = 'LAMBDA0'; format = '4096E'
        name = 'DLAMBDA'; format = '241664E'; dim = '( 4096, 59)'
        name = 'LAMBDAX'; format = '6D'
        name = 'TILTX'; format = '3D'
        name = 'SLITFN'; format = '59E'
        name = 'DLAM'; format = '177E'; dim = '( 59, 3)'
        name = 'INFOMASK'; format = '241664J'; dim = '( 4096, 59)'
    )
    >>> hdulist[2].data.columns
    ColDefs(
        name = 'AMP'; format = 'E'
        name = 'CEN'; format = 'E'
        name = 'SIG'; format = 'E'
        name = 'BASE'; format = 'E'
        name = 'MASK'; format = 'B'
    )

MOSViz needs Flux and Uncertainty so the relevant columns are `FLUX` and `IVAR` in the the first `slit` extension.

.. code-block:: python
    
    >>> hdulist[1].data['FLUX'].shape
    (1, 59, 4096)
    >>> hdulist[1].data['IVAR'].shape
    (1, 59, 4096)
    >>>

All of our arrays are the same size but they are stored in 3 dimensional arrays (with the first axis of size 1). 
So we'll just take the first (and only) element which will give a 2D array.

We also need a WCS which should be in the header of the same extension as the data.

.. code-block:: python

    >>> from astropy.wcs import WCS
    >>> WCS(hdulist[1].header)

    Number of WCS axes: 2
    CTYPE : 'LAMBDA'  'LAMBDA'
    CRVAL : 6450.6538154  0.0
    CRPIX : 0.0  0.0
    CD1_1 CD1_2  : 0.32103118300400002  0.0
    CD2_1 CD2_2  : 0.0  1.0
    NAXIS    : 4367352 1

The WCS is here however, the two axes both have name 'LAMBDA' and if we look at look at the second coordinate we can see that it isn't actually transformed.
Glue expects that all of a `Data` object's components (including WCS axes) have unique name.
We can take of this easily in the data loader function.

Now that we know what data we want from our FITS files let's look at how to write the data loader function.

.. code-block:: python

    @data_factory('DEIMOS 2D Spectrum')

The `@data_factory` decorator tells Glue that this is a function used to load data.

.. code-block:: python
    
    def deimos_spectrum2D_reader(file_name):

The function itself takes a filename to open as its only argument.  
The function name `deimos_spectrum2D_reader` is what will go into the header of catalog file to tell MOSViz how to load 2D spectra.

.. code-block:: python

        hdulist = fits.open(file_name)
        data = Data(label='2D Spectrum')

Now as above we're going to open the FITS file.  
Then we instantiate a Glue `Data` object which will be populated with the data we wish to pass to MOSViz.

.. code-block:: python

        hdulist[1].header['CTYPE2'] = 'Spatial Y'
        data.coords = coordinates_from_wcs(WCS(hdulist[1].header))
        data.header = hdulist[1].header

As we noted above, the WCS axes should have different names.
Since the second axis is not transformed we'll just change the header keyword which specifies its name to 'Spatial Y'
Then we set the `coords` attribute of the `Data` object with `coordinates_from_wcs`.
We also pass the FITS header to the data so that useful information can be displayed in the MOSViz.

.. code-block:: python

        data.add_component(hdulist[1].data['FLUX'][0], 'Flux')
        data.add_component(hdulist[1].data['IVAR'][0], 'Uncertainty')

        return data

As stated above, MOSViz expects the Flux and Uncertainty to be each be a single 2D array.
We take the first component of each array (a 2D array) pass them to the `data` object using the `add_component()` method.

+++++++++++++++++++
Cutout Image Reader
+++++++++++++++++++

.. code-block:: python

    @data_factory('ACS Cutout Image')
    def acs_cutout_image_reader(file_name):
        """
        Data loader for the ACS cut-outs for the DEIMOS spectra.

        The cutouts contain only the image.
        """

        hdulist = fits.open(file_name)
        data = Data(label='ACS Cutout Image')
        data.coords = coordinates_from_header(hdulist[0].header)
        data.header = hdulist[0].header
        data.add_component(hdulist[0].data, 'Flux')

        return data

MOSViz expects the Cutout Image Data object to have one component: Flux.
Since it is an image it also expects a World Coordinate System (WCS) which tells it how to transform from pixels to sky coordinates.  
Let's take a look at the contents of our example FITS file to see which parts we need to pass to MOSViz.

.. code-block:: python

    >>> from astropy.io import fits
    >>> hdulist = fits.open('12020821.acs.i_6ac_.fits')
    >>> hdulist.info()
    Filename: 12020821.acs.i_6ac_.fits
    No.    Name         Type      Cards   Dimensions   Format
    0    PRIMARY     PrimaryHDU      71   (201, 201)   float32
    >>> hdulist[0].data.shape
    (201, 201)

There is only one extensions and the data in it is the cutout image (a 2D array).

We also need a WCS which should be in the header of the same extension as the data.

.. code-block:: python

    >>> from astropy.wcs import WCS
    >>> WCS(hdulist[0].header)
    WCS Keywords

    Number of WCS axes: 2
    CTYPE : 'RA---TAN'  'DEC--TAN'
    CRVAL : 214.40388488799999  52.630077362100003
    CRPIX : 101.70472905800101  100.94206076200101
    CD1_1 CD1_2  : -8.3333331279300006e-06  -4.5781947460699999e-14
    CD2_1 CD2_2  : -4.5781947460699999e-14  8.3333331279300006e-06
    NAXIS    : 201 201

The WCS looks as we would expect.

Now that we know what data we want from our FITS files let's look at how to write the data loader function.

.. code-block:: python

    @data_factory('ACS Cutout Image')

The `@data_factory` decorator tells Glue that this is a function used to load data.

.. code-block:: python
    
    def acs_cutout_image(file_name):

The function itself takes a filename to open as its only argument.  
The function name `acs_cutout_image` is what will go into the header of catalog file to tell MOSViz how to load the cutout image.

.. code-block:: python

        hdulist = fits.open(file_name)
        data = Data(label='Cutout Image')

Now as above we're going to open the FITS file.  
Then we instantiate a Glue `Data` object which will be populated with the data we wish to pass to MOSViz.

.. code-block:: python

        data.coords = coordinates_from_wcs(WCS(hdulist[0].header))
        data.header = hdulist[0].header

We set the `coords` attribute of the `Data` object with `coordinates_from_wcs`.
We also pass the FITS header to the data so that useful information can be displayed in the MOSViz.

.. code-block:: python

        data.add_component(hdulist[0].data, 'Flux')

        return data

We take the data in first extension data array (a 2D array) and pass it to the `data` object using the `add_component()` method.

The full contents of the ~/.glue/config.py is shown below

.. code-block:: python

    from glue.config import data_factory
    from glue.core import Data
    from glue.core.coordinates import coordinates_from_header, coordinates_from_wcs
    from astropy.io import fits
    from astropy.wcs import WCS
    import numpy as np

    @data_factory('DEIMOS 1D Spectrum')
    def deimos_spectrum1D_reader(file_name):
        """
        Data loader for Keck/DEIMOS 1D spectra.

        This loads the 'Bxspf-B' (extension 1)
        and 'Bxspf-R' (extension 2) and appends them
        together to proudce the combined Red/Blue Spectrum
        along with their Wavelength and Inverse Variance
        arrays.
        """

        hdulist = fits.open(file_name)
        data = Data(label='1D Spectrum')
        data.header = hdulist[1].header

        full_wl = np.append(hdulist[1].data['LAMBDA'][0], hdulist[2].data['LAMBDA'][0])
        full_spec = np.append(hdulist[1].data['SPEC'][0], hdulist[2].data['SPEC'][0])
        full_ivar = np.append(hdulist[1].data['IVAR'][0], hdulist[2].data['IVAR'][0])

        data.add_component(full_wl, 'Wavelength')
        data.add_component(full_spec, 'Flux')
        data.add_component(full_ivar, 'Uncertainty')

        return data

    @data_factory('DEIMOS 2D Spectrum')
    def deimos_spectrum2D_reader(file_name):
        """
        Data loader for Keck/DEIMOS 2D spectra.

        This loads only the Flux and Inverse variance.
        Wavelength information comes from the WCS.
        """

        hdulist = fits.open(file_name)
        data = Data(label='2D Spectrum')
        data.coords = coordinates_from_header(hdulist[1].header)
        data.header = hdulist[1].header
        data.add_component(hdulist[1].data['FLUX'][0], 'Flux')
        data.add_component(hdulist[1].data['IVAR'][0], 'Uncertainty')
        return data

    @data_factory('ACS Cutout Image')
    def acs_cutout_image_reader(file_name):
        """
        Data loader for the ACS cut-outs for the DEIMOS spectra.

        The cutouts contain only the image.
        """

        hdulist = fits.open(file_name)
        data = Data(label='ACS Cutout Image')
        data.coords = coordinates_from_header(hdulist[0].header)
        data.header = hdulist[0].header
        data.add_component(hdulist[0].data, 'Flux')

        return data
