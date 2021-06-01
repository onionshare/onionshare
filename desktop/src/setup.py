#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
import setuptools

version = "2.3.2"

setuptools.setup(
    name="onionshare",
    version=version,
    description=(
        "OnionShare lets you securely and anonymously send and receive files. It works by starting a web "
        "server, making it accessible as a Tor onion service, and generating an unguessable web address so "
        "others can download files from you, or upload files to you. It does _not_ require setting up a "
        "separate server or using a third party file-sharing service."
    ),
    author="Micah Lee",
    author_email="micah@micahflee.com",
    maintainer="Micah Lee",
    maintainer_email="micah@micahflee.com",
    url="https://onionshare.org",
    license="GPLv3",
    keywords="onion, share, onionshare, tor, anonymous, web server",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Flask",
        "Topic :: Communications :: File Sharing",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
    ],
    packages=[
        "onionshare",
        "onionshare.tab",
        "onionshare.tab.mode",
        "onionshare.tab.mode.share_mode",
        "onionshare.tab.mode.receive_mode",
        "onionshare.tab.mode.website_mode",
        "onionshare.tab.mode.chat_mode",
    ],
    package_data={
        "onionshare": [
            "resources/*",
            "resources/images/*",
            "resources/locale/*",
        ]
    },
    entry_points={
        "console_scripts": [
            "onionshare = onionshare:main",
        ],
    },
)
