# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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
from PyQt5 import QtCore, QtWidgets, QtGui
import platform, subprocess, sys, os

from onionshare import strings

class TorSubprocess(QtCore.QThread):
    log = QtCore.pyqtSignal(str)

    def __init__(self):
        super(TorSubprocess, self).__init__()

        # Find the path to the Tor binary
        s = platform.system()
        if s == 'Windows':
            root_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            self.tor_path = os.path.join(os.path.join(os.path.join(root_path, 'tor'), 'Tor'), 'tor.exe')
        elif s == 'Darwin':
            # TODO: not implemented yet
            pass

    def run(self):
        # Open tor in a subprocess and monitor its output
        p = subprocess.Popen([self.tor_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = p.stdout.readline()
            if line != '':
                self.log.emit(line.decode())
            else:
                break

class TorDialog(QtWidgets.QDialog):
    """
    Tor dialog.
    """
    def __init__(self, parent=None):
        super(TorDialog, self).__init__(parent)

        self.setModal(False)
        self.setWindowTitle(strings._('gui_tor_window_title', True))

        # Tor log
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)

        # Buttons
        close_button = QtWidgets.QPushButton(strings._('gui_tor_button_close', True))
        close_button.clicked.connect(self.close_clicked)
        restart_button = QtWidgets.QPushButton(strings._('gui_tor_button_restart', True))
        restart_button.clicked.connect(self.restart_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(close_button)
        buttons_layout.addWidget(restart_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.log)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def start(self):
        # Start the Tor subprocess
        self.t = TorSubprocess()
        self.t.log.connect(self.log_line)
        self.t.start()

        # Show the dialog
        self.exec_()

    def log_line(self, line):
        self.log.moveCursor(QtGui.QTextCursor.End)
        self.log.insertPlainText(line)
        self.log.moveCursor(QtGui.QTextCursor.End)

    def close_clicked(self):
        """
        Hide the Tor dialog.
        """
        self.hide()

    def restart_clicked(self):
        pass
