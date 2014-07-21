# import stuff for pyinstaller to find
import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect, base64, random, functools, logging
from PyQt4 import QtCore, QtGui, QtWebKit
import stem, stem.control, flask
import onionshare, onionshare_gui

onionshare_gui.main()
