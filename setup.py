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
        'eeweather==0.3.24',
        'numpy==1.23.2',
        'pandas<=1.5.3',
        'scipy==1.10.0',
        'sqlalchemy<=1.4.46',
        'zipcodes==1.2.0',
        'loguru',
        'pgeocode==0.4.1',
        ],
)
