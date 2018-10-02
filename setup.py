#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

# Where the magic happens:
setup(
    name='led-control',
    version='0.1.0',
    description='WS2812 LED controller with web interface for Raspberry Pi',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='jackw01',
    python_requires='>=3.3.0',
    url='https://github.com/jackw01/led-control',
    packages=find_packages(),
    install_requires=[
        'Flask>=1.0.2'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ledcontrol=ledcontrol:main'
        ]
    },
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ]

)
