from setuptools import setup, find_packages

version = __import__('thermostat').get_version()

long_description = "Calculate connected thermostat temperature/run-time savings."

setup(name='thermostat',
    version=version,
    description='Calculate connected thermostat savings',
    long_description=long_description,
    url='https://github.com/impactlab/thermostat/',
    author='Phil Ngo',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='thermostat savings EPA',
    packages=find_packages(),
    install_requires=[
        'eemeter',
        'pandas',
        ],
)
