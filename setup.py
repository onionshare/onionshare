#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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
    """OnionShare lets you securely and anonymously send and receive files. It """
    """works by starting a web server, making it accessible as a Tor onion """
    """service, and generating an unguessable web address so others can download """
    """files from you, or upload files to you. It does _not_ require setting up """
    """a separate server or using a third party file-sharing service."""
)
long_description = description + "\n\n" + (
    """If you want to send files to someone, OnionShare hosts them on your own """
    """computer and uses a Tor onion service to make them temporarily accessible """
    """over the internet. The receiving user just needs to open the web address """
    """in Tor Browser to download the files. If you want to receive files, """
    """OnionShare hosts an anonymous dropbox directly on your computer and uses """
    """a Tor onion service to make it temporarily accessible over the internet. """
    """Other users can upload files to you from by loading the web address in """
    """Tor Browser."""
)
author = 'Micah Lee'
author_email = 'micah@micahflee.com'
url = 'https://github.com/micahflee/onionshare'
license = 'GPL v3'
keywords = 'onion, share, onionshare, tor, anonymous, web server'
classifiers = [
        "Programming Language :: Python :: 3",
        "Framework :: Flask",
        "Topic :: Communications :: File Sharing",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Environment :: Web Environment"
    ]
data_files=[
        (os.path.join(sys.prefix, 'share/applications'), ['install/onionshare.desktop']),
        (os.path.join(sys.prefix, 'share/metainfo'), ['install/onionshare.appdata.xml']),
        (os.path.join(sys.prefix, 'share/pixmaps'), ['install/onionshare80.xpm']),
        (os.path.join(sys.prefix, 'share/onionshare'), file_list('share')),
        (os.path.join(sys.prefix, 'share/onionshare/images'), file_list('share/images')),
        (os.path.join(sys.prefix, 'share/onionshare/locale'), file_list('share/locale')),
        (os.path.join(sys.prefix, 'share/onionshare/templates'), file_list('share/templates')),
        (os.path.join(sys.prefix, 'share/onionshare/static/css'), file_list('share/static/css')),
        (os.path.join(sys.prefix, 'share/onionshare/static/img'), file_list('share/static/img')),
        (os.path.join(sys.prefix, 'share/onionshare/static/js'), file_list('share/static/js'))
    ]
if platform.system() != 'OpenBSD':
    data_files.append(('/usr/share/nautilus-python/extensions/', ['install/scripts/onionshare-nautilus.py']))

setup(
    name='onionshare', version=version,
    description=description, long_description=long_description,
    author=author, author_email=author_email, maintainer=author, maintainer_email=author_email,
    url=url, license=license, keywords=keywords, classifiers=classifiers,
    packages=[
        'onionshare',
        'onionshare.web',
        'onionshare_gui',
        'onionshare_gui.mode',
        'onionshare_gui.mode.share_mode',
        'onionshare_gui.mode.receive_mode',
        'onionshare_gui.mode.website_mode'
    ],
    include_package_data=True,
    scripts=['install/scripts/onionshare', 'install/scripts/onionshare-gui'],
    data_files=data_files
)
