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


class Uploads(QtWidgets.QScrollArea):
    """
    The uploads chunk of the GUI. This lists all of the active upload
    progress bars, as well as information about each upload.
    """
    def __init__(self, common):
        super(Uploads, self).__init__()
        self.common = common

        self.uploads = {}

        self.setWindowTitle(strings._('gui_uploads', True))
        self.setWidgetResizable(True)
        self.setMaximumHeight(600)
        self.setMinimumHeight(150)
        self.setMinimumWidth(350)
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setWindowFlags(QtCore.Qt.Sheet | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.CustomizeWindowHint)
        self.vbar = self.verticalScrollBar()

        uploads_label = QtWidgets.QLabel(strings._('gui_uploads', True))
        uploads_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        self.no_uploads_label = QtWidgets.QLabel(strings._('gui_no_uploads', True))

        self.uploads_layout = QtWidgets.QVBoxLayout()

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(uploads_label)
        layout.addWidget(self.no_uploads_label)
        layout.addLayout(self.uploads_layout)
        layout.addStretch()
        widget.setLayout(layout)
        self.setWidget(widget)

    def reset(self):
        """
        Reset the uploads back to zero
        """
        pass
