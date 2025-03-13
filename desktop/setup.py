#!/usr/bin/env python3
# This file is used to build the Snapcraft and Flatpak packages
from setuptools import setup

# The version must be hard-coded because Snapcraft won't have access to ../cli
version = "2.6.3"

setup(
    name="onionshare",
    version=version,
)
