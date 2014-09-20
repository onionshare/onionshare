#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
from glob import glob

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def file_list(path):
    files = []
    for filename in os.listdir(path):
        if os.path.isfile(path+'/'+filename):
            files.append(path+'/'+filename)
    return files


version = open('version').read().strip()

setup(
    name='onionshare',
    version=version,
    description='OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file.',
    long_description="""OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.""",
    author='Micah Lee',
    author_email='micah@micahflee.com',
    url='https://github.com/micahflee/onionshare',
    license="GPL v3",
    keywords='onion, share, onionshare, tor, anonymous, web server',
    packages=['onionshare', 'onionshare_gui'],
    include_package_data=True,
    scripts=['bin/onionshare', 'bin/onionshare-gui'],
    data_files=[
        (os.path.join(sys.prefix, 'share/applications'), ['setup/onionshare.desktop']),
        (os.path.join(sys.prefix, 'share/pixmaps'), ['setup/onionshare80.xpm']),
        (os.path.join(sys.prefix, 'share/onionshare/images'), [
            'images/logo.png',
            'images/drop_files.png',
            'images/server_stopped.png',
            'images/server_started.png',
            'images/server_working.png'
        ]),
        (os.path.join(sys.prefix, 'share/onionshare/locale'), [
            'locale/de.json',
            'locale/en.json',
            'locale/es.json',
            'locale/fi.json',
            'locale/fr.json',
            'locale/it.json',
            'locale/nl.json',
            'locale/no.json',
            'locale/pt.json',
            'locale/ru.json',
            'locale/tr.json'
        ])
    ]
)

