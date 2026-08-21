# Configuration lives in pyproject.toml. This shim only keeps the legacy
# `python setup.py ...` invocations working; prefer `python -m build`.
from setuptools import setup

setup()
