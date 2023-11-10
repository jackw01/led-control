#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, io
from setuptools import find_packages, setup, Extension
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call

def pre_install():
    print('preinstall')
    if is_raspberrypi():
        check_call('scons', cwd='ledcontrol/driver/rpi_ws281x/')

class PreDevelopCommand(develop):
    def run(self):
        pre_install()
        develop.run(self)

class PreInstallCommand(install):
    def run(self):
        pre_install()
        install.run(self)

def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except Exception:
        pass
    return False

requirements = [
    'Flask==2.2.2',
    'RestrictedPython>=5.2',
    'sacn>=1.8.1',
    'HAP-python==4.4.0',
    'pyopenssl==22.1.0',
    'numpy>=1.21.0',
    'pyserial>=3.5',
    'Werkzeug==2.2.2',
] + (['bjoern>=3.2.1'] if sys.platform.startswith('linux') else []) + (['pyfastnoisesimd>=0.4.2'] if not is_raspberrypi() else [])

extensions = [
    Extension('_ledcontrol_rpi_ws281x_driver',
              sources=['ledcontrol/driver/ledcontrol_rpi_ws281x_driver_wrap.c'],
              include_dirs=['ledcontrol/driver'],
              library_dirs=['ledcontrol/driver/rpi_ws281x/'],
              libraries=['ws2811'])
]

setup(
    name='led-control',
    version='2.0.0',
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
    ext_modules=extensions if is_raspberrypi() else [],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ledcontrol=ledcontrol:main'
        ]
    },
    cmdclass={
        'develop': PreDevelopCommand,
        'install': PreInstallCommand,
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
