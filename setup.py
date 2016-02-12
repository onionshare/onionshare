#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2015 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, platform

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def file_list(path):
    files = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            files.append(os.path.join(path, filename))
    return files

system = platform.system()
version = open('version').read().strip()

description = (
    """OnionShare lets you securely and anonymously share a file of any size with someone. """
    """It works by starting a web server, making it accessible as a Tor hidden service, """
    """and generating an unguessable URL to access and download the file.""")

long_description = description + " " + (
    """It doesn't require setting up a server on the internet somewhere or using a third """
    """party filesharing service. You host the file on your own computer and use a Tor """
    """hidden service to make it temporarily accessible over the internet. The other user """
    """just needs to use Tor Browser to download the file from you."""
)

images = [
    'images/logo.png',
    'images/drop_files.png',
    'images/server_stopped.png',
    'images/server_started.png',
    'images/server_working.png'
]

locale = [
    'locale/cs.json',
    'locale/de.json',
    'locale/en.json',
    'locale/eo.json',
    'locale/es.json',
    'locale/fi.json',
    'locale/fr.json',
    'locale/it.json',
    'locale/nl.json',
    'locale/no.json',
    'locale/pt.json',
    'locale/ru.json',
    'locale/tr.json'
]

if system == 'Linux':
    setup(
        name='onionshare',
        version=version,
        description=description,
        long_description=long_description,
        author='Micah Lee',
        author_email='micah@micahflee.com',
        url='https://github.com/micahflee/onionshare',
        license="GPL v3",
        keywords='onion, share, onionshare, tor, anonymous, web server',
        packages=['onionshare', 'onionshare_gui'],
        include_package_data=True,
        scripts=['install/linux_scripts/onionshare', 'install/linux_scripts/onionshare-gui'],
        data_files=[
            (os.path.join(sys.prefix, 'share/applications'), ['install/onionshare.desktop']),
            (os.path.join(sys.prefix, 'share/appdata'), ['install/onionshare.appdata.xml']),
            (os.path.join(sys.prefix, 'share/pixmaps'), ['install/onionshare80.xpm']),
            (os.path.join(sys.prefix, 'share/onionshare'), ['version']),
            (os.path.join(sys.prefix, 'share/onionshare/images'), images),
            (os.path.join(sys.prefix, 'share/onionshare/locale'), locale)
        ]
    )

elif system == 'Darwin':
    setup(
        name='OnionShare',
        version=version,
        description=description,
        long_description=long_description,
        app=['install/osx_scripts/onionshare-gui'],
        data_files=[
            ('images', images),
            ('locale', locale),
            ('html', ['onionshare/index.html', 'onionshare/404.html']),
            ('', ['version'])
        ],
        options={
            'py2app': {
                'argv_emulation': True,
                'iconfile': 'install/onionshare.icns',
                'extra_scripts': ['install/osx_scripts/onionshare'],
                'includes': [
                    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
                    'jinja2', 'jinja2.ext', 'jinja2.ext.autoescape', 'sip']
            }
        },
        setup_requires=['py2app', 'flask', 'stem'],
    )
