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
import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect, base64, random, functools, logging, ctypes, hmac, shutil
from itertools import izip
import stem, stem.control, flask
from PyQt4 import QtCore, QtGui

import onionshare, onionshare_gui

onionshare_gui.main()
