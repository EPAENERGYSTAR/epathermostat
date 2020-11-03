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
    ],
    keywords='thermostat savings EPA',
    packages=find_packages(),
    package_data={'': ['*.csv', '*.json']},
    install_requires=[
        'eemeter==2.5.2',
        'eeweather==0.3.23',
        'pandas==0.25.3',
        'sqlalchemy==1.3.1',
        'zipcodes==1.1.2',
        ],
)
