# Changelog

## Alpha Releases (version 2.0 release)

### Version 2.0 (alpha)

* Changed metadata file format
    - Equipment types now denote type and stages of equipment
* Changed interval file format
    - Moved to hourly timestamp instead of daily timestamp format
* Added certification file
* Added import error logging to log thermostat and reason for rejection
* Removed year end-to-end and mid-to-mid calculations
* Added multiprocessor support for stats module
* Improved error logging
* Removed eemeter
* Updated logic to use ZIP Code for weather station lookup and climate zone lookup
* Updated Climate Zone lookup strategy

## Production releases

### Version 1.7.3 (2021-04-30)

* Bugfix: Updates setup.py to prevent numpy versions that are incompatible (1.20 and later)

### Version 1.7.2 (2020-05-28)

* Backport warning suppression from 2.x branch
* Fix tests / test coverage

### Version 1.7.1 (2020-01-09)

* This release has been updated to support Python 3.7. Also includes fixes for zip codes beginning with zero, and caching improvements.

### Version 1.7.0 (2019-06-07)

* Changeover in duty cycle to calculate using total hours (on and off) in denominator. For example, aux duty cycle is now `aux_runtime (in bin) / total_hours (in bin)`.
* Changeover Resistance Heating Filtering routines to use top 5% filter, instead of previous filter using `1.5 * IQR`.

### Version 1.6.0 (2019-04-22)

* Weather retrieval updates: eeweather 0.3.13 , eemeter 2.5.2. Pipenv support.
* RHU: alternate bin spacing, duty cycle outputs, min runtime for bin inclusion (RHU2 calculation), IQR outlier filtering for RHU2.
    - Retain original bin groups (00 deg F – 60 deg F by 5 degrees),
    - Added `<10 deg F, 10-20, 20-30, 30-40, 40-50, 50-60 deg F`

* Add an RHU2 calculation which has the following structure changes
    - A given thermostat must have at least (>=) `VAR_MIN_RHU_RUNTIME` hours of Total (any) runtime within a RHU temp bin for this bin to be counted /used. Otherwise, reset this bin as if no runtime had occurred (i.e. zero out that bin).
    - `Bin_i`. (Not use unless): `Runtime_BIN_I {Comp + Aux + Emergency} >= VAR_MIN_RT`
    - Set `VAR_MIN_RHU_RUNTIME` in the code to 30 hours.

* Update quantile bins output by software:
    - Current : q10 -- q90 (by 10)
    - New (Updated): q1,q2.5,q5,q10 – q90 (by 5), q95,q98,q99

* Spacing / Bin Groupings: Duty Cycles, Code should return additional new variable outputs
    - Aux Duty Cycle (Aux Runtime / Total Runtime)
    - Emergency Duty Cycle (Emergency Runtime / Total Runtime)
    - Compressor Duty Cycle (Compressor Runtime / Total Runtime)
        + 1: By Each Temperature Bin (both groupings)
        + 2: Additional Summary Result, overall per thermostat

* Statistics Module Changes
- New aggregation rules in stats rollup. Applies ONLY to RHU2.
- Drop all RHU data from aggregation(s) where `data result > Median ± 1.5 * IQR` of value in rollup calculations (e.g. rollup by climate zone)
* DROP warnings for np (Numpy) divide by zero in RHU calculations, since this is an expected state for thermostats (climate zones would not span the full list of temps).

### Version 1.5.1 (2018-08-20)

* Reworked selecting stations using ZCTA instead of Zip codes
* Allows for saving eemeter cache into a json file
* Fixes deadlock issue with eemeter / eeweather cache not being present

### Version 1.5.0 (Not released. Changes incorporated in 1.5.1)

* Added improved logging using Python logging system
* Added flags to quiet particularly verbose error messages

### Version 1.4.0 fix (2018-07-16)

* Stability fixes for divide-by-zero issue
* Fixes for test cases failing
* Fixes for weather station lookup
* Added sample code to scripts directory

### Version 1.4.0 (2018-04-24)

* Multiple processor support for calculations
* Multiple requests for ISDN data
* Mean Interior and Exterior Core Temperature Output
* Reorganized files

### Version 1.3.0 (2018-04-05)

* Updated to Python 3.6
* Updated UTC to take an integer offset
* Updated for Pandas 0.22 compatibility
* Updated code to better handle division-by-zero errors

### Version 1.1.2 (2017-10-24)

* Update to Pandas 0.20.3
* Changed to use constants for magic numbers
* Additional bugfixes

### Version 1.1.1 (2017-10-23)

* Bugfixes

### Version 1.0 (2016-11-23)

* Initial production release
