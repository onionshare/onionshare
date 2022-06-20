#!/usr/bin/env python3
# This file is used to build the Snapcraft and Flatpak packages
import setuptools

# The version must be hard-coded because Snapcraft won't have access to ../cli
version = "2.6"

setuptools.setup(
    name="onionshare",
    version=version,
    description="Securely and anonymously share files, host websites, and chat with friends using the Tor network",
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
