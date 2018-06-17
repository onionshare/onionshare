#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2018 Micah Lee <micah@micahflee.com>

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

import os, sys, platform, tempfile
from distutils.core import setup

def file_list(path):
    files = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            files.append(os.path.join(path, filename))
    return files

version = open('share/version.txt').read().strip()
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
author = 'Micah Lee'
author_email = 'micah@micahflee.com'
url = 'https://github.com/micahflee/onionshare'
license = 'GPL v3'
keywords = 'onion, share, onionshare, tor, anonymous, web server'
data_files=[
        (os.path.join(sys.prefix, 'share/applications'), ['install/onionshare.desktop']),
        (os.path.join(sys.prefix, 'share/appdata'), ['install/onionshare.appdata.xml']),
        (os.path.join(sys.prefix, 'share/pixmaps'), ['install/onionshare80.xpm']),
        (os.path.join(sys.prefix, 'share/onionshare'), file_list('share')),
        (os.path.join(sys.prefix, 'share/onionshare/images'), file_list('share/images')),
        (os.path.join(sys.prefix, 'share/onionshare/locale'), file_list('share/locale')),
        (os.path.join(sys.prefix, 'share/onionshare/html'), file_list('share/html')),
    ]
if platform.system() != 'OpenBSD':
    data_files.append(('/usr/share/nautilus-python/extensions/', ['install/scripts/onionshare-nautilus.py']))

setup(
    name='onionshare', version=version,
    description=description, long_description=long_description,
    author=author, author_email=author_email,
    url=url, license=license, keywords=keywords,
    packages=['onionshare', 'onionshare_gui'],
    include_package_data=True,
    scripts=['install/scripts/onionshare', 'install/scripts/onionshare-gui'],
    data_files=data_files
)
