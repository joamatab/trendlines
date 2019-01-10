# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

requires = [
    "flask>=1.0",
    "peewee>=3.8",
]

setup(
    name="trendlines",
    version="0.0.0",
    description="Lightweight time-series recording.",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/dougthor42/trendlines",
    author="Douglas Thor",
    author_email="doug.thor@gmail.com",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=False,
    python_requires=">=3.5",
    install_requires=requires,
)
