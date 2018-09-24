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
import time
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


class Connection(object):
    def __init__(self, common, connection_id):
        self.common = common

        self.connection_id = connection_id
        self.started = time.time()


class Connections(QtWidgets.QScrollArea):
    """
    The downloads chunk of the GUI. This lists all of the active download
    progress bars.
    """
    def __init__(self, common):
        super(Connections, self).__init__()
        self.common = common

        self.connections = {}

        self.setWindowTitle(strings._('gui_publishing'))
        self.setWidgetResizable(True)
        self.setMinimumHeight(150)
        self.setMinimumWidth(350)
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setWindowFlags(QtCore.Qt.Sheet | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.CustomizeWindowHint)
        self.vbar = self.verticalScrollBar()
        self.vbar.rangeChanged.connect(self.resizeScroll)

        connections_label = QtWidgets.QLabel(strings._('gui_publishing'))
        connections_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        self.no_connections_label = QtWidgets.QLabel(strings._('gui_no_publishing'))
        self.clear_history_button = QtWidgets.QPushButton(strings._('gui_clear_history'))
        self.clear_history_button.clicked.connect(self.reset)
        self.clear_history_button.hide()

        self.connections_layout = QtWidgets.QVBoxLayout()

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(connections_label)
        layout.addWidget(self.no_connections_label)
        layout.addWidget(self.clear_history_button)
        layout.addLayout(self.connections_layout)
        layout.addStretch()
        widget.setLayout(layout)
        self.setWidget(widget)


    def resizeScroll(self, minimum, maximum):
        """
        Scroll to the bottom of the window when the range changes.
        """
        self.vbar.setValue(maximum)


    def add(self, connection_id, total_bytes):
        """
        Add a new connection progress bar.
        """
        # Hide the no_connections_label
        self.no_connections_label.hide()
        # Show the clear_history_button
        self.clear_history_button.show()

        # Add it to the list
        connection = Connection(self.common, connection_id)
        self.connections[connection_id] = connection


    def reset(self):
        """
        Reset the connections back to zero
        """

        self.connections = {}

        self.no_connections_label.show()
        self.clear_history_button.hide()
        self.resize(self.sizeHint())
