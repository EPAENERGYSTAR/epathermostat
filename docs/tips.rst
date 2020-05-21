Helpful Tips
============

Performance Improvements
------------------------

These are tips that may improve the performance of the application depending on your environment.

* Installing `numexpr` may give significant performance boosts on multi-core machines and large data sets. It may be installed via `pip install numexpr` in the same virtual environment as `thermostat`.

* Installing `bottleneck` may help improve performance with datasets that have large numbers of `np.nan` entries. It may be installed via `pip install bottleneck` in the same virtual environment as `thermostat`.

Debugging data issues
---------------------

* Missing thermostats are logged just after the importer script finishes running. It checks what thermostats are in the metadata file and which thermostats were actually loaded. Any missing thermostats are reported by the ID given in the metadata file. The reasons for the thermostat being rejected are logged as they occur to the screen and any log files.
