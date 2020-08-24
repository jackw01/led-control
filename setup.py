#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup, Extension

requirements = [
    'recordclass>=0.12.0.1',
    'Flask>=1.0.2',
    'RestrictedPython>=4.0',
    'ujson>=3.1.0',
]

setup(
    name='led-control',
    version='1.0.0',
    description='WS2812 LED strip controller with web interface for Raspberry Pi',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='jackw01',
    python_requires='>=3.7.0',
    url='https://github.com/jackw01/led-control',
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
    setup_requires=requirements,
    ext_modules=[
        Extension('_rpi_ws281x',
                  sources=['ledcontrol/rpi_ws281x/lib/rpi_ws281x_wrap.c'],
                  include_dirs=['ledcontrol/rpi_ws281x/lib'],
                  library_dirs=['ledcontrol/rpi_ws281x/lib/c/rpi_ws281x/'],
                  libraries=['ws2811'])
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
