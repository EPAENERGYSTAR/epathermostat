from setuptools import setup, find_packages, Command

version = __import__('thermostat').get_version()

long_description = "Calculate connected thermostat temperature/run-time savings."

setup(name='thermostat',
    version=version,
    description='Calculate connected thermostat savings',
    long_description=long_description,
    url='https://github.com/EPAENERGYSTAR/epathermostat',
    author='Phil Ngo',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    keywords='thermostat savings EPA',
    packages=find_packages(),
    package_data={'': ['*.csv', '*.json']},
    python_requires='>=3.11',
    install_requires=[
        # Reshaped eeweather (WeatherStation/WeatherLocation API), the upstream
        # feature branch this 1.8.0 preview targets. It declares its own deps
        # (numpy, pandas>=2.2, platformdirs, pyproj, requests, shapely) and no
        # longer needs attrs/sqlalchemy.
        # NOTE: the static-by-year GHCNh transport that makes fetches survive
        # the NOAA dynamic-API outage is a pending PR against this branch; until
        # it merges, live fetches route through the (currently down) dynamic API.
        'eeweather @ git+https://github.com/opendsm/eeweather.git@feature/power-source',
        'numpy>=2,<3',
        'pandas>=2.2,<3',
        'scipy>=1.11',
        'requests',
        'python-dateutil',
        ],
)
