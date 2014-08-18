from __future__ import division
import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect, base64, random, functools, logging, ctypes
import stem, stem.control, flask, itsdangerous
from PyQt4 import QtCore, QtGui

import onionshare, onionshare_gui

onionshare_gui.main()
