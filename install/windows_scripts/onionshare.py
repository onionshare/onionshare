# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
from __future__ import division
import os, subprocess, time, hashlib, platform, json, locale, socket
import argparse, queue, inspect, base64, random, functools, logging, ctypes
import hmac, shutil
import stem, stem.control, flask
from PyQt5 import QtCore, QtWidgets, QtGui

import onionshare, onionshare_gui

# Disable py2exe logging in Windows. Comment these if you need logs. See:
# http://www.py2exe.org/index.cgi/StderrLog
# http://stackoverflow.com/questions/20549843/py2exe-generate-log-file
import sys
f = open(os.devnull, 'w')
sys.stdout = f
sys.stderr = f

onionshare_gui.main()
