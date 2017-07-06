************
Installation
************

MOSViz is distributed through the `Anaconda <https://anaconda.org>`_ package
manager. Specifically, it lives within Space Telescope Science Institute's
`AstroConda <https://astroconda.readthedocs.io/>`_ channel.

If you do not have Anaconda, please follow the `instructions here
<https://www.continuum.io/downloads>`_ to install it, or scroll down for
manual installation of MOSViz.


Install via Anaconda
--------------------

If you have AstroConda setup, then all you have to do to install SpecViz is
simply type the following at any Bash terminal prompt::

    $ conda install mosviz

If you do not have AstroConda setup, then you can install SpecViz by
specifying the channel in your install command::

    $ conda install --channel http://ssb.stsci.edu/astroconda mosviz

At this point, you can simply load a MOS catalog into Glue and view the data
via the newly-installed MosViz Viewer.

Install via source
------------------

MosViz can also be installed manually using the source code and requires the
following dependencies to be installed on your system. Most of these will be
handled automatically by the setup functions.

* Python 3 (recommended) or Python 2
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

SpecViz functionality
---------------------

MOSViz comes with the ability to open 1D spectra inside a SpecViz instance
within Glue. However, this functionality will only be enabled if you also have
SpecViz installed on your system.

If you are interested in this functionality, please follow the `SpecViz
installation instructions <http://specviz.readthedocs.io/en/latest/>`_.
