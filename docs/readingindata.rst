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
