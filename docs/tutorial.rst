Quickstart
==========

Installation
------------

To install the thermostat package for the first time, we highly recommend that
you create a virtual environment or a conda environment in which to install it.
You may choose to skip this step, but do so at the risk of corrupting your
existing python environment. Isolating your python environment will also
make it easier to debug.

.. code-block:: bash

    # if using virtualenvwrapper (see https://virtualenvwrapper.readthedocs.org/en/latest/install.html)
    $ mkvirtualenv thermostat
    (thermostat)$ pip install thermostat

    # if using Python 3 with venv (see https://docs.python.org/3/library/venv.html)
    # (cd to directory with data files)
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv)$ pip install thermostat

    # if using conda (see note below - conda is distributed with Anaconda)
    $ conda create --yes --name thermostat pandas
    $ source activate thermostat
    (thermostat)$ pip install thermostat

    # If using pipenv (see https://github.com/pypa/pipenv)
    # (cd to directory with data files)
    $ pipenv --python 3.7 install thermostat

If you already have an environment, use the following:

.. code-block:: bash

    # if using virtualenvwrapper
    $ workon thermostat
    (thermostat)$

    # if using conda
    $ source activate thermostat
    (thermostat)$

To deactivate the environment when you've finished, use the following:

.. code-block:: bash

    # if using virtualenvwrapper / venv / pipenv
    (thermostat)$ deactivate
    $

    # if using conda
    (thermostat)$ source deactivate
    $

Check to make sure you are on the most recent version of the package.

.. code-block:: python

    >>> import thermostat; thermostat.get_version()

    '1.7.2'

If you are not on the correct version, you should upgrade:

.. code-block:: bash

    $ pip install thermostat --upgrade

The command above will update dependencies as well. If you wish to skip this,
use the :code:`--no-deps` flag:

.. code-block:: bash

    $ pip install thermostat --upgrade --no-deps

Previous versions of the package are available on `github <https://github.com/EPAENERGYSTAR/epathermostat/releases>`_.

.. note::

    If you experience issues installing python packages with C extensions, such
    as `numpy` or `scipy`, we recommend installing and using the free
    `Anaconda <https://www.continuum.io/downloads>`_ Python distribution by
    Continuum Analytics. It contains many of the numeric and scientific
    packages used by this package and has installers for Python 2.7 and 3.5 for
    Windows, Mac OS X and Linux.

Once you have verified a correct installation, import the necessary methods
and set a directory for finding and storing data.

.. note::

    If you suspect a package version conflict or error, you can verify the
    versions of the packages you have installed against the package
    versions in :download:`thermostatreqnotes.txt <../thermostatreqnotes.txt>`.

    To list your package versions, use:

    .. code-block:: bash

        $ pip freeze

    or (if you're using Anaconda):

    .. code-block:: bash

        $ conda list

Script setup and imports
------------------------

Import the few built-in python packages and methods we will be using in
this tutorial as follows.

.. code-block:: python

    import sys
    import os
    import warnings
    from os.path import expanduser

Also make sure to import the methods we will be using from the thermostat
package.

.. code-block:: python

    from thermostat.importers import from_csv
    from thermostat.exporters import metrics_to_csv
    from thermostat.stats import compute_summary_statistics
    from thermostat.stats import summary_statistics_to_csv


If you wish to use multiple processors for your thermostat calculations you'll
need some additional modules:

.. code-block:: python

    from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics


Set the `data_dir` variable as a convenience. We will refer to this directory
and save our results in it. You should also move all downloaded and extracted
files used in this tutorial into this directory before using them. You may, of
course, choose to use a different directory, which you can set here, or
override it entirely by replacing it where it appears in the tutorial.

.. code-block:: python

    data_dir = os.path.join(expanduser("~"), "thermostat_tutorial")
    # or data_dir = "/full/path/to/custom/directory/"

Optional Setup
--------------

If you wish to follow the progress of downloading and caching external weather
files, which will be the most time-consuming portion of this tutorial, you may
wish at this point to configure logging. The example here will work within most
iPython / Jupyter Notebook or script environments. If you have a more
complicated logging setup, you may need to use something other than the root
logger, which this uses.

.. code-block:: python

    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

.. note::

    The thermostat package depends on the eemeter and eeweather packages for weather data
    fetching. The eeweather package automatically creates its own cache directory
    in which it keeps cached versions of weather source data. This speeds up
    the (generally I/O bound) NOAA weather fetching routine on subsequent
    internal calls to fetch the same weather data (i.e. getting outdoor
    temperature data for thermostats that map to the same weather station).

    For more information, see the `eeweather package <http://eeweather.openee.io/en/latest/index.html>`_.

.. note::

    US Census Bureau ZIP Code Tabulation Areas (ZCTA) are used to map USPS ZIP
    codes to outdoor temperature data. If the automatic mapping is unsuccessful
    for one or more of the ZIP codes in your dataset, the reason is likely to
    be the discrepancy between "true" USPS ZIP codes and the US Census Bureau
    ZCTAs. "True" ZIP codes are not used because they do not always map well to
    location (for example, ZIP codes for P.O. boxes). You may need to first map
    ZIP codes to ZCTAs, or these thermostats will be skipped. There are roughly
    32,000 ZCTAs and roughly 42000 ZIP codes - many fewer ZCTAs than ZIP codes.

Computing individual thermostat-season metrics
----------------------------------------------

After importing the package methods, load the example thermostat data, or
provide data of your own. See :ref:`thermostat-input` for more detailed file
format information.

Fabricated example data from 35 thermostats in various climate zones, is
available for download :download:`here <./examples/examples.zip>`.

Loading the thermostat data below will take more than a few minutes, even if
the weather cache is enabled (see note above). This is because loading
thermostat data involves downloading hourly weather data from a remote
source - in this case, the NCDC.

The following loads an lazy iterator over the thermostats. The thermostats
will be loaded into memory as necessary in the following steps.

.. code-block:: python

    metadata_filename = os.path.join(data_dir, "examples/metadata.csv")
    thermostats = from_csv(metadata_filename, verbose=True)

To calculate savings metrics, iterate through thermostats and save the results.
Uncomment the commented lines if you would like to store the thermostats in
memory for inspection. Note that this could eat up your application memory and
is only recommended for debugging purposes.

.. code-block:: python

    metrics = []
    # saved_thermostats = []
    for thermostat in thermostats:
        outputs = thermostat.calculate_epa_field_savings_metrics()
        metrics.extend(outputs)
        # saved_thermostats.append(thermostat)


If you are looking to use multiple thermostats for the calculation you may
replace the above code with the following method call:

.. code-block:: python

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

This will use all of the available CPUs on the machine in order to calculate
the savings metrics. 

.. note::

    You will need to have imported the
    ``multiple_thermostat_calculate_epa_field_savings_metrics`` method from
    ``thermostat.multiple`` prior to using this method.

    If you're running under Windows please see the "Notes for Windows Users" below.


The single-thermostat metrics should be output to CSV and converted to dataframe format.

.. code-block:: python

    output_filename = os.path.join(data_dir, "thermostat_example_output.csv")
    metrics_df = metrics_to_csv(metrics, output_filename)

The output CSV will be saved in your data directory and should very nearly
match the output CSV provided in the example data.

See :ref:`thermostat-output` for more detailed file format information.


Computing summary statistics
----------------------------

Once you have obtained output for each individual thermostat in your dataset,
use the stats module to compute summary statistics, which are formatted for
submission to the EPA. The example below works with the output file from the
tutorial above and can be modified to use your data.

Compute statistics across all thermostats.

.. code-block:: python

    # uses the metrics_df created in the Quickstart above.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # uses the metrics_df created in the quickstart above.
        stats = compute_summary_statistics(metrics_df)

        # If you want to have advanced filter outputs, use this instead
        # stats_advanced = compute_summary_statistics(metrics_df, advanced_filtering=True)

Save these results to file.

Each row of the saved CSV will represent one type of output, with one row per
statistic per output. Each column in the CSV will represent one subset of
thermostats, as determined by grouping by EIC climate zone and applying
various filtering methods. National weighted averages will be available near
the top of the file.

At this point, you will also need to provide an alphanumeric product identifier
for the connected thermostat; e.g. a combination of the connected thermostat
service plus one or more connected thermostat device models that comprises the
data set.

.. code-block:: python

    product_id = "INSERT ALPHANUMERIC PRODUCT ID HERE"
    stats_filepath = os.path.join(data_dir, "thermostat_example_stats.csv")
    stats_df = summary_statistics_to_csv(stats, stats_filepath, product_id)

    # or with advanced filter outputs
    # stats_advanced_filepath = os.path.join(data_dir, "thermostat_example_stats_advanced.csv")
    # stats_advanced_df = summary_statistics_to_csv(stats_advanced, stats_advanced_filepath, product_id)

National savings are computed by weighted average of percent savings results
grouped by climate zone. Heavier weights are applied to results in climate
zones which, regionally, tend to have longer runtimes. Weightings used are
available :download:`for download <../thermostat/resources/NationalAverageClimateZoneWeightings.csv>`.

Notes for Windows Users
-----------------------

Python under Windows requires that all multiprocessing code needs to be run under a sub module. If you are under Windows you will need to wrap your code using the following:

.. code-block:: python
    
    def main():
        # Code goes here

    if __name__ == "__main__":
        main()

Not having this wrapper will cause a Runtime Error "Attempt to start a new process before the current process has finished its bootstrapping phase.".

Other platforms should not be affected by this.

More information
----------------

For additional information on package usage, please see the
:ref:`thermostat-api` documentation. For additional information in the input and output data files please see the :ref:`thermostat-input` and :ref:`thermostat-output` documentation.
