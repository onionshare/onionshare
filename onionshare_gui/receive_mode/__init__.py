# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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

from onionshare import strings

from ..server_status import ServerStatus

class ReceiveMode(QtWidgets.QWidget):
    """
    Parts of the main window UI for receiving files.
    """
    def __init__(self, common, qtapp, app, web, status_bar, server_share_status_label, system_tray):
        super(ReceiveMode, self).__init__()
        self.common = common
        self.qtapp = qtapp
        self.app = app
        self.web = web

        self.status_bar = status_bar
        self.server_share_status_label = server_share_status_label
        self.system_tray = system_tray

        # Server status
        self.server_status = ServerStatus(self.common, self.qtapp, self.app, self.web)

        # Primary action layout
        primary_action_layout = QtWidgets.QVBoxLayout()
        primary_action_layout.addWidget(self.server_status)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(primary_action_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.primary_action)
        self.setLayout(layout)

    def timer_callback(self):
        """
        This method is called regularly on a timer while receive mode is active.
        """
        pass
