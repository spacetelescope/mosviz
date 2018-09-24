************
Installation
************

MOSViz is packaged in the Conda environment system and therefore 
requires Miniconda to be installed. This makes it reasonably simple 
to install MOSViz along with all its dependencies.

If you do not have Miniconda, please follow the `instructions here
<https://conda.io/miniconda.html>`_ to install it, or scroll down for
manual installation of MOSViz.


Install via Conda
-----------------

Once you have Miniconda installed, then all you have to do to install MOSViz is
simply type the following at any Bash terminal prompt::

    $ conda create -n <environment_name> -c glueviz mosviz

Next activate your MOSViz conda environment::

    $ conda activate <environment_name>

To launch MOSViz now you enter::

    $ mosviz

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

SpecViz functionality
---------------------

MOSViz comes with the ability to open 1D spectra inside a SpecViz instance
within Glue. However, this functionality will only be enabled if you also have
SpecViz installed on your system.

If you are interested in this functionality, please follow the `SpecViz
installation instructions <http://specviz.readthedocs.io/en/latest/>`_.
