***************************
Getting Started with MOSViz
***************************

This page will walk you through the basics of the MOSViz GUI. Once you have MOSViz 
`installed <https://mosviz.readthedocs.io/en/latest/installation.html>`_ you can 
launch the GUI by typing:

`$ mosviz`

.. figure::  images/empty_mosviz_view.png
   :align:   center
   Figure 1: A screenshot of the MOSViz GUI.

++++++++++++
Opening Data
++++++++++++

There are many ways to open a dataset with MOSViz:

* A catalog of targets in tabular form
* By selecting the **Open Data Set** item under the **File** menu or using the equivalent shortcut (e.g. **Ctrl+O** on Linux, **Cmd+O** on Mac).
* Dragging and dropping data files on the main window.

We will use
a dataset from the `Deimos <https://www2.keck.hawaii.edu/inst/deimos/>`_ 
instrument at the Keck Observatory. The main components of a MOSViz 
dataset are:

* A 2D image cutout
* A 2D spectrum
* A 2D spectrum

++++++++++++++++
Visualizing Data
++++++++++++++++

When the dataset is loaded in the data collection, drag and drop the dataset 
from the data collection to the visualization dashboard. A dialog will appear asking you 
to select a data viewer, select the **MOSViz viewer**. Next you will be prompted with
another dialog asking you to specify the different viewers for each component
of your dataset. This dialog will also contains options to overlay slit positions.

.. figure::  images/mosviz_data_dialog.png
   :align:   center
   Figure 2: MOSViz GUI with Deimos multiobject spectroscopy dataset opened in view.

Once your configuration is set, click OK. Now the visualization dashboard should contain
an image cutout, a 2D spectrum and a 1D specturm.

.. figure::  images/mosviz_data_dialog.png
   :align:   center
   Figure 2: MOSViz GUI with Deimos multiobject spectroscopy dataset opened in view.
