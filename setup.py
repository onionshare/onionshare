#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='onionshare',
    version='0.1',
    description='OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file.',
    long_description="""OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.""",
    author='Micah Lee',
    author_email='micah@micahflee.com',
    url='https://github.com/micahflee/onionshare',
    include_package_data=True,
    install_requires=[
        'flask >= 0.10.1',
        'stem >= 1.1.1'
    ],
    license="GPL v3",
    keywords='onion, share, onionshare, tor, anonymous, web server',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GPL License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],
    packages=['onionshare'],
    scripts=['bin/onionshare', 'bin/tails-onionshare']
)
