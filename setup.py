from setuptools import setup, find_packages, Command

version = __import__('thermostat').get_version()

long_description = "Calculate connected thermostat temperature/run-time savings."

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([sys.executable, 'runtests.py', '--runslow', '--cov-report', 'term-missing', '--cov', 'thermostat'  ])
        raise SystemExit(errno)


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
    cmdclass = {'test': PyTest},
    keywords='thermostat savings EPA',
    packages=find_packages(),
    install_requires=[
        'eemeter==0.3.20',
        'pandas==0.18.1',
    ],
)
