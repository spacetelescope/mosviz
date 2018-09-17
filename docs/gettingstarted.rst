***************************
Getting Started with MOSViz
***************************

This page will walk you through the basics of the MOSViz GUI. Once you have MOSViz 
`installed <https://mosviz.readthedocs.io/en/latest/installation.html>`_ you can 
launch the GUI by typing:

`$ mosviz`

.. image:: images/empty_mosviz_view.png
   :align: center

++++++++++++
Opening Data
++++++++++++

There are many ways to open a dataset with MOSViz:

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
of your dataset. This dialog will also contains options to overlay slit positions. For 
this example we are going to use the default settings.

.. image:: images/mosviz_data_dialog.png
   :align: center

Once your configuration is set, click OK. Now the visualization dashboard should contain
an image cutout, a 2D spectrum and a 1D specturm.

.. image:: images/mosviz_deimos_data.png
   :align: center

To view the other spectra and cutouts from the data table, use the Next/Previous buttons
or select by name using the drop down located in the upper left hand corner of the MOSViz Viewer.