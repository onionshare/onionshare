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
from setuptools import setup


def file_list(path):
    files = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            files.append(os.path.join(path, filename))
    return files


version = open("share/version.txt").read().strip()
description = (
    """OnionShare is an open source tool for securely and anonymously sending and """
    """receiving files and publishing websites using Tor onion services. It works by """
    """starting a web server directly on your computer and making it accessible as """
    """an unguessable Tor web address that others can load in Tor Browser. It """
    """doesn't require setting up a separate server, using a third party service, or """
    """even logging into an account."""
)
author = "Micah Lee"
author_email = "micah@micahflee.com"
url = "https://github.com/micahflee/onionshare"
license = "GPL v3"
keywords = "onion, share, onionshare, tor, anonymous, web server"
classifiers = [
    "Programming Language :: Python :: 3",
    "Framework :: Flask",
    "Topic :: Communications :: File Sharing",
    "Topic :: Security :: Cryptography",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Intended Audience :: End Users/Desktop",
    "Operating System :: OS Independent",
    "Environment :: Web Environment",
]
data_files = [
    ("share/applications", ["install/org.onionshare.OnionShare.desktop"],),
    ("share/icons/hicolor/scalable/apps", ["install/org.onionshare.OnionShare.svg"],),
    ("share/metainfo", ["install/org.onionshare.OnionShare.appdata.xml"],),
    ("share/onionshare", file_list("share")),
    ("share/onionshare/images", file_list("share/images")),
    ("share/onionshare/locale", file_list("share/locale")),
    ("share/onionshare/templates", file_list("share/templates"),),
    ("share/onionshare/static/css", file_list("share/static/css"),),
    ("share/onionshare/static/img", file_list("share/static/img"),),
    ("share/onionshare/static/js", file_list("share/static/js"),),
]
if not platform.system().endswith("BSD") and platform.system() != "DragonFly":
    data_files.append(
        (
            "share/nautilus-python/extensions/",
            ["install/scripts/onionshare-nautilus.py"],
        )
    )

setup(
    name="onionshare",
    version=version,
    description=description,
    author=author,
    author_email=author_email,
    maintainer=author,
    maintainer_email=author_email,
    url=url,
    license=license,
    keywords=keywords,
    classifiers=classifiers,
    packages=[
        "onionshare",
        "onionshare.web",
        "onionshare_gui",
        "onionshare_gui.tab",
        "onionshare_gui.tab.mode",
        "onionshare_gui.tab.mode.share_mode",
        "onionshare_gui.tab.mode.receive_mode",
        "onionshare_gui.tab.mode.website_mode",
    ],
    entry_points={
        "console_scripts": [
            "onionshare = onionshare:main",
            "onionshare-gui = onionshare_gui:main",
        ],
    },
    data_files=data_files,
)
