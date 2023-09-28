#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
import sys
import platform
import shutil
import cx_Freeze
from cx_Freeze import setup, Executable
from setuptools import find_packages

# Discover the version
with open(os.path.join("..", "cli", "onionshare_cli", "resources", "version.txt")) as f:
    version = f.read().strip()
    # change a version like 2.6.dev1 to just 2.6, for cx_Freeze's sake
    last_digit = version[-1]
    if version.endswith(f".dev{last_digit}"):
        version = version[0:-5]

# Build
include_files = [(os.path.join("..", "LICENSE"), "LICENSE")]

if platform.system() == "Windows":
    include_msvcr = True
    gui_base = "Win32GUI"
    # gui_base = None
    exec_icon = os.path.join("onionshare", "resources", "onionshare.ico")

elif platform.system() == "Darwin":
    include_msvcr = False
    gui_base = None
    exec_icon = None

elif platform.system() == "Linux":
    include_msvcr = False
    gui_base = None
    exec_icon = None

    if not shutil.which("patchelf"):
        print("Install the patchelf package")
        sys.exit()

setup(
    name="onionshare",
    version=version,
    description="Securely and anonymously share files, host websites, and chat with friends using the Tor network",
    packages=find_packages(
        where=".",
        include=["onionshare"],
        exclude=["package", "screenshots", "scripts", "tests"],
    ),
    options={
        # build_exe, for Windows and macOS
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
                "PySide6",
                "PySide6.QtCore",
                "PySide6.QtGui",
                "PySide6.QtWidgets",
            ],
            "excludes": [
                "test",
                "tkinter",
                "PySide6.Qt3DAnimation",
                "PySide6.Qt3DCore",
                "PySide6.Qt3DExtras",
                "PySide6.Qt3DInput",
                "PySide6.Qt3DLogic",
                "PySide6.Qt3DRender",
                "PySide6.QtCharts",
                "PySide6.QtConcurrent",
                "PySide6.QtDataVisualization",
                "PySide6.QtHelp",
                "PySide6.QtLocation",
                "PySide6.QtMultimedia",
                "PySide6.QtMultimediaWidgets",
                "PySide6.QtNetwork",
                "PySide6.QtOpenGL",
                "PySide6.QtOpenGLFunctions",
                "PySide6.QtPositioning",
                "PySide6.QtPrintSupport",
                "PySide6.QtQml",
                "PySide6.QtQuick",
                "PySide6.QtQuickControls2",
                "PySide6.QtQuickWidgets",
                "PySide6.QtRemoteObjects",
                "PySide6.QtScript",
                "PySide6.QtScriptTools",
                "PySide6.QtScxml",
                "PySide6.QtSensors",
                "PySide6.QtSerialPort",
                "PySide6.QtSql",
                "PySide6.QtTest",
                "PySide6.QtTextToSpeech",
                "PySide6.QtUiTools",
                "PySide6.QtWebChannel",
                "PySide6.QtWebEngine",
                "PySide6.QtWebEngineCore",
                "PySide6.QtWebEngineWidgets",
                "PySide6.QtWebSockets",
                "PySide6.QtXml",
                "PySide6.QtXmlPatterns",
            ],
            "include_files": include_files,
            "include_msvcr": include_msvcr,
        },
        # bdist_mac, making the macOS app bundle
        "bdist_mac": {
            "iconfile": os.path.join("onionshare", "resources", "onionshare.icns"),
            "bundle_name": "OnionShare",
            "plist_items": [
                ("CFBundleShortVersionString", version),
                ("CFBundleVersion", version),
            ],
        },
    },
    executables=[
        Executable(
            "package/onionshare.py",
            base=gui_base,
            icon=exec_icon,
        ),
        Executable(
            "package/onionshare-cli.py",
            base=None,
            icon=exec_icon,
        ),
    ],
)
