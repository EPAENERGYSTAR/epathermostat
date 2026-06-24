from setuptools import setup, find_packages, Command

try:
    version = __import__('thermostat').get_version()
except ImportError:
    version = '1.7.6'

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
    ],
    keywords='thermostat savings EPA',
    packages=find_packages(),
    package_data={'': ['*.csv', '*.json']},
    install_requires=[
        'eemeter==3.1.0',
        'eeweather==0.3.30',
        'sqlalchemy',
        'attrs',
        'pytz',
        'pandas>=1.0,<2',
        'numpy>=1.20,<2',
        ],
)
