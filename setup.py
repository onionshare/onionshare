#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

packages = ['onionshare', 'onionshare_gui']

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
    packages=packages,
    include_package_data=True,
    scripts=['bin/onionshare', 'bin/onionshare-gui'],
    data_files=[
        ('/usr/share/applications', ['setup/onionshare.desktop']),
        ('/usr/share/pixmaps', ['setup/onionshare80.xpm'])
    ]
)

