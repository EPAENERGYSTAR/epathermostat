Gremlin Data Removal Script
===========================

.. _gremlin-data-removal-script:

This is a script for testing the effects of missing data on a dataset. This script randomly removes five days from the dataset to simulate random days of missing data from the sample.

This script is not intended for data submission. This is purely for research into data-quality issues.

How to use the gremlin script
-----------------------------

The ``gremlin.py`` script is located under the ``scripts`` directory on the ``feature/epa2.0_gremlin`` git branch. You will need to checkout the epathermostat source from `GitHub`_ using a command similar to the following:

.. code-block:: bash

    craig@kryten:~/projects$ git clone https://github.com/EPAENERGYSTAR/epathermostat.git
    Cloning into 'epathermostat'...
    remote: Enumerating objects: 3945, done.
    ...

    craig@kryten:~/projects$ cd epathermostat
    craig@kryten:~/projects/epathermostat$ git checkout feature/epa2.0_gremlin 
    Branch 'feature/epa2.0_gremlin' set up to track remote branch 'feature/epa2.0_gremlin' from 'origin'.
    Switched to a new branch 'feature/epa2.0_gremlin'
    craig@kryten:~/projects/epathermostat$ 


Next we'll go to the ``scripts`` directory, where the ``gremlin.py`` script is located:

.. code-block:: bash

    craig@kryten:~/projects/epathermostat$ cd scripts/
    craig@kryten:~/projects/epathermostat/scripts$ 
   

From there we can edit the ``gremlin.py`` script and give it the location of our data. Locate the ``DATA_DIR`` variable near to the top of the file and give it the location of your data. The default is to use the test data directory for single-stage equipment. This will give you an idea of how the program works, but you'll want to change this to a location containing your version 2.0-compliant interval data to get the full benefit of this script.

.. code-block:: python

    DATA_DIR = os.path.join("..", "tests", "data", "single_stage")


So, if our data was in ``/home/craig/projects/thermostat_data`` we could use the following:

.. code-block:: python

    DATA_DIR = os.path.join('/', 'craig', 'projects', 'thermostat_data')

or even

.. code-block:: python

    DATA_DIR = '/home/craig/projects/thermostat_data'

Either format is fine. (We use the ``os.path.join`` for portability between different operating systems, but if that's not a concern then please use what works best for you).

We'll also need to create a virtual environment to run our code. For this example I'm going to use Python3's built-in venv.

.. code-block:: bash

    craig@kryten:~/projects/epathermostat/scripts$ cd ..
    craig@kryten:~/projects/epathermostat$ python3.9 -m venv venv
    craig@kryten:~/projects/epathermostat$ source venv/bin/activate
    (venv) craig@kryten:~/projects/epathermostat$ 


For ``conda`` we use the following:

.. code-block:: bash

    (base) ubuntu@conda:~$ conda create --yes --name thermostat pip
    Collecting package metadata (current_repodata.json): done
    Solving environment: done 
    ...

    (base) ubuntu@conda:~$ conda activate thermostat
    (thermostat) ubuntu@conda:~$ 


We'll then install the epathermostat 2.0 software.

.. code-block:: bash

    (venv) craig@kryten:~/projects/epathermostat$ pip install -e .
    Obtaining file:///home/craig/projects/epathermostat
    Collecting eemeter==3.1.0
    Using cached eemeter-3.1.0-py2.py3-none-any.whl (584 kB)
    Collecting eeweather==0.3.24
    Using cached eeweather-0.3.24-py2.py3-none-any.whl (4.1 MB)
    Collecting numpy
    ...
    Successfully installed certifi-2021.5.30 charset-normalizer-2.0.4 click-8.0.1 eemeter-3.1.0 eeweather-0.3.24 greenlet-1.1.1 idna-3.2 numpy-1.21.2 pandas-1.3.2 patsy-0.5.1 pyproj-3.1.0 python-dateutil-2.8.2 pytz-2021.1 requests-2.26.0 scipy-1.7.1 shapely-1.7.1 six-1.16.0 sqlalchemy-1.4.23 statsmodels-0.12.2 thermostat-2.0.0a4 urllib3-1.26.6 zipcodes-1.1.2
    (venv) craig@kryten:~/projects/epathermostat$


If you have the latest version of epathermosat 2.0 installed on your system you may use that instead, however the ``feature/epa2.0_gremlin`` branch will have the latest code releases applied to it, so we recommend creating a new environment and using that for your testing.

Next, run the ``gremlin.py`` code:

.. code-block:: bash

    (venv) craig@kryten:~/projects/epathermostat/scripts$ python gremlin.py 
    2021-09-02 11:11:29,458 - root - INFO - Metadata randomized to prevent collisions in cache.
    2021-09-02 11:11:29,483 - thermostat.importers - INFO - Importing thermostat 1ab401c3-8588-4568-b012-e5d22941edad
    ...

The code will create a new metrics database (default: ``metrics.db`` in the same directory as the ``gremlin.py`` script.

The script takes a while to run so please be patient.

What it's doing
---------------

The script will run through each of the loaded thermostats. For each of the thermostats it will create a list of the days in the dataset and randomize that list. It will them iterate through the randomized list of days and remove a number of those days from the dataset (default is 5). The software logs which days are removed from the sample. It then also writes out the metrics results to the database. 

Graphing the data
-----------------

In order to visualize the results you'll want to graph the data.

You'll need to have matplotlib installed. You can install it via the following command (Conda users will need to use ``conda`` in order to install matplotlib.)

.. code-block:: bash

   (venv) craig@kryten:~/projects/epathermostat/scripts$ pip install matplotlib
   Collecting matplotlib
   ...

   Installing collected packages: pyparsing, pillow, kiwisolver, cycler, matplotlib
   Successfully installed cycler-0.10.0 kiwisolver-1.3.2 matplotlib-3.4.3 pillow-8.3.1 pyparsing-2.4.7
   (venv) craig@kryten:~/projects/epathermostat/scripts$ 

Once you have matplotlib installed you can use the following command to graph the data:

.. code-block:: bash

   (venv) craig@kryten:~/projects/epathermostat/scripts$ python missing_data_results_export.py 

This should generate two files called ``change_in_cooling_savings_vs_core_days.png`` and ``change_in_heating_savings_vs_core_days`` in the scripts directory.

Once you have those files please send them to the Energy Star smart thermostat team.

.. _GitHub: https://github.com/EPAENERGYSTAR/epathermostat
