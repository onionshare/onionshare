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
import os
from cx_Freeze import setup, Executable

with open(os.path.join("..", "cli", "onionshare_cli", "resources", "version.txt")) as f:
    version = f.read().strip()

setup(
    name="onionshare",
    version=version,
    description="Securely and anonymously share files, host websites, and chat with friends using the Tor network",
    options={
        "build_exe": {
            "packages": [
                "cffi",
                "engineio",
                "engineio.async_drivers.gevent",
                "engineio.async_drivers.gevent_uwsgi",
                "gevent",
                "jinja2.ext",
                "onionshare",
                "onionshare_cli",
            ],
            "excludes": ["test", "tkinter"],
            "include_files": [("..\LICENSE", "LICENSE")],
            "include_msvcr": True,
        }
    },
    executables=[
        Executable(
            "package/onionshare.py",
            # base="Win32GUI",
            base=None,
            icon=os.path.join("onionshare", "resources", "onionshare.ico"),
        ),
        Executable(
            "package/onionshare-cli.py",
            base=None,
            icon=os.path.join("onionshare", "resources", "onionshare.ico"),
        ),
    ],
)
