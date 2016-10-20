**************************************
Overview of Basic MOSViz Functionality
**************************************

MOSViz is composed of separate components that interact via “linked views.”  As described below, and as shown in Figures 1, MOSViz includes a:

•	1D spectral viewer

•	2D spectral viewer

•	Image cutout viewer

•	Data table

•	2D scatter plot

•	3D scatter plot, and a

•	mosaic viewer where the targets are indicated.  

Each of these components is described in more detail below.  Once a MOS data set is read in, users can use any combination of these tools.  Use cases with work flows are given in Section 8, but a typical workflow is the following:

•	Read in a table of coordinated (RA, DEC) and star-formation rates, cutout images for a single waveband, and 2D and 1D spectra for 1000 galaxies at a redshift of 2

•	Sort galaxies in table according to star-formation rate

•	Highlight the 3 galaxies with the highest star-formation rates

•	This causes the spectra and image of the first galaxy to display

•	Measure the equivalent width of an emission line in the first galaxy

•	Its value will propagate to the information box and the table

•	Hit the arrow button (or press a tab key) in the spectral viewer to move to the next galaxy

•	Do the same for the second and third objects

•	Make a different selection in the table (e.g.,galaxies with the lowest star-formation rates)

•	Write notes on these targets in the information box

•	Write out new table

•	Quit MOSViz

MOSViz’s main functionality is to help users to visually inspect and perform a “first-look” analysis of multiple spectra.  To this 
end, MOSViz’s main component is its 1D and 2D spectral viewers. The user can choose to use both 1D and 2D viewers, or either one.  
For the 1D spectra, the full functionality of SpecViz, as described in a future Technical Report, will be available.  Users can 
interact with the 1D and 2D spectra, making measurements of e.g, emission and absorption line strengths and sky continuum levels, 
and noting results in the information box (described below).  Users can plot indicators on the spectra showing locations where they 
expect spectral lines to appear based on built-in or user-supplied line lists.   Users will be able to read-in template spectra to compare with and fit to.  Functionality such as smoothing and convolving will be available.  For NIRSpec MSA data, the user will be able to scroll through UNC, saturation, and DQ planes.  Batch mode fitting may be enabled in future versions of MOSViz. For the 2D spectra, a basic set of view adjustments will be available: zoom, pan, colormap, and intensity scaling. The UI will read back the row, column and flux under in the pixel under the cursor. 

MOSViz also includes an optional cutout viewer to show images of each target alongside their 1D and 2D spectra.   The cutout is aligned so that the cross-dispersion direction has the same vertical orientation as for the 2D spectrum. We provide documentation on how to create such cutouts for single-waveband images and multi-band color images, as described in Section 7.2.  Multiple cutouts from large images for different wavebands can be shown in MOSViz.  For the single-waveband cutouts, a basic set of view adjustments will be available: zoom, pan, colormap, and intensity scaling. The UI will read back the row, column and flux under in the pixel under the cursor.. In addition, we provide documentation on how to show overlayed spectral apertures on each cutout image (typically source and background).  For most MOS’s, the spectral aperture is a thin slit.  For the NIRSpec MSA, it is a single or multi-shutter “slitlet” (see Section 7.3.3 and Figure 7.3-1 of Böeker et al. 2012).  In addition, for the NIRSpec MSA, we also document how to demarcate sky apertures on the cutout images.  

While the user can adjust the layout, the default will have the wavelength axis of the 1D and 2D aligned and locked so that they zoom and pan together, and will have the cross-dispersion spatial axis locked to the cutout vertical axis so that they zoom and pan together. All of the data must have valid WCSs for this to work, which will often some pre-processing of non-JWST data sets. We will provide documentation and helper tools to simplify this.

The data table allows users to select targets to display in the spectral and/or cutout viewers.  Optionally, they can also display the selected targets in the 2D and/or 3D scatter plots and/or on the large image viewer.  Columns in the data table must include at minimum target identification (id), right ascension (RA), and declination (DEC).  The table can include any other quantities the user wishes to include.  Its columns can be sorted.  The user can select as many or as few objects as they wish to display.  

The optional mosaic viewer shows an image of the area of sky surveyed by the MOS.  Targets are indicated.  The user can select a single target by clicking on it, or multiple contiguous targets by selecting a region on the image.  As with the data table, the selections are sent to the spectra and/or cutout viewers, and they can also be shown on the scatter plots and large image viewer.

The optional 2D and 3D scatter plots can be used to plot the quantities in the tables.   The user can click on each point/target in the plots to display the selected target’s spectra and images.  The user can select multiple contiguous points/targets at once.

Finally, the information box displays the information from the table on the specific target displayed.  The user is able to enter additional information into the information box that will be added to the table.
