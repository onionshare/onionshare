# import stuff for pyinstaller to find
import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect, base64, random, functools, logging
import PyQt4.QtCore, PyQt4.QtGui, PyQt4.QtWebKit
import stem, stem.control, flask
import onionshare, onionshare_gui

onionshare_gui.main()
