# Release Checklist

This is a document of the steps that will need to occur to create a new release of the EPA Thermostat Software. These steps will ensure that the software is updated and built correctly for those who use it.

## First Things First

Clone the repository and switch to the latest branch that needs to be built (usually this is a release branch, using [gitflow](https://nvie.com/posts/a-successful-git-branching-model/) parlance. In this checklist we'll use `release/2.0.1` but you will need to update that with whatever version you're using.

`git clone git@github.com:EPAENERGYSTAR/epathermostat.git`

or, if you're not using SSH,

`git clone https://github.com/EPAENERGYSTAR/epathermostat.git`

Create the release branch:

`git flow release start 2.0.1`

You will need to create a Virtual Environment. This can be achieved with the following command:

`cd path/to/epathermostat`

`python3 -m venv venv`

`source path/to/epathermostat/venv/bin/activate`

## Update packages

Verify if any packages have been updated. The main packages that will need to be kept current are `zipcodes` and `eeweather`, as they'll have the information needed for zipcode lookups and weather station / climate zone mapping.

If any packages have been updated please update them in the `setup.py` file and commit the file using `git commit`

## Prep for verification / build

Run `pip install -e .` to install the dependencies for epathermostat. (This command _must_ be executed from the epathermostat path, and with the venv virtual environment activated)

Run `pip install -r dev-requirements.txt` to install the developer requirements.

## Update the ZIPCodes / Weather Stations

Head to the scripts directory and run the following command to update the `zipcodes_lookup.py` file. (This file contains the up-to-date zipcode to climate zone / weather station mapping based on `eeweather` and `zipcodes`.)

`cd scripts`

`bash build_zipcodes_lookup.sh`

This will build a Python file that contains a data structure for zip code lookups. Once complete add the updated files (if any) to the release branch using `git add` and `git commit`.

(Note: `zipcodes` 1.2.0 reports its version number as 1.1.3. This is a known issue).

## Update the package version

Edit the `thermostat/__init__.py` file and update the VERSION string to the current version.

## Ensure tests are running

`pytest`

## Build the source distribution

`python setup.py sdist`

## Finish the release branch and push to github

`git flow feature finish`

`git push origin --tags`

## Upload to the file to PyPI

`cd sdist`

`twine upload sdist/epathermostat-2.0.1.tar.gz`

## Head to github to create a new release.

Follow the instructions at [https://github.com/EPAENERGYSTAR/epathermostat/releases/new](https://github.com/EPAENERGYSTAR/epathermostat/releases/new).
