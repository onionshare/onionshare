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

from onionshare import common

class Alert(QtWidgets.QMessageBox):
    """
    An alert box dialog.
    """
    def __init__(self, message, icon=QtWidgets.QMessageBox.NoIcon, buttons=QtWidgets.QMessageBox.Ok, autostart=True):
        super(Alert, self).__init__(None)
        self.setWindowTitle("OnionShare")
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setText(message)
        self.setIcon(icon)
        self.setStandardButtons(buttons)

        if autostart:
            self.exec_()
