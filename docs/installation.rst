************
Installation
************

MOSViz is packaged and distributed through both Anaconda via the GlueViz
channel, as well as through the Python Package Index (PyPI). It is also
available from source.


Install via Conda
-----------------

In order to use the Anaconda package, you must first install an
Anaconda distribution. If you do not have Anaconda, please follow the
`instructions here <https://www.anaconda.com/download>`_ to install it.

Once you have Anaconda installed, all you have to do to install MOSViz is
simply type the following at any Bash terminal prompt::

    $ conda create -n <environment_name> -c glueviz mosviz

Next activate your MOSViz conda environment::

    $ conda activate <environment_name>

To launch MOSViz now you enter::

    $ mosviz


Install via PyPI
----------------

To install MOSViz using PyPI type the following at any terminal prompt::

    $ pip install mosviz

You will also need to install the PyQt package as well by typing the following::

    $ pip install pyqt5


Install via source
------------------

.. warning::
    Using the Conda install is the preferred method for installing MOSViz to ensure
    that all dependencies are met. If you install via source/pip be aware that
    some dependencies will need to be installed manually!

MosViz can also be installed manually using the source code and requires the
following dependencies to be installed on your system. Most of these will be
handled automatically by the setup functions.

* Python 3
* Astropy
* Numpy
* Scipy
* Matplotlib
* Specutils
* Glue

At your terminal, you may either clone the repository directly and then
install::

    $ git clone https://github.com/spacetelescope/mosviz.git
    $ cd mosviz
    $ python setup.py install

Or, have the `pip <http://pip.pypa.org>`_ package manager do everything for you::

    $ pip install git+https://github.com/spacetelescope/mosviz.git

Either way, the MosView Viewer should show up in the list of available Glue
viewers.

Alternatively, you can use conda and install a nightly build using::

    $ conda create -n mosviz-nightly -c glueviz/label/dev python=3.6 mosviz


SpecViz functionality
---------------------

MOSViz comes with the ability to open 1D spectra inside a SpecViz instance
within Glue. However, this functionality will only be enabled if you also have
SpecViz installed on your system.

If you are interested in this functionality, please follow the `SpecViz
installation instructions <http://specviz.readthedocs.io/en/latest/>`_.
