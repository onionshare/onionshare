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

class Alert(QtWidgets.QMessageBox):
    """
    An alert box dialog.
    """
    def __init__(self, common, message, icon=QtWidgets.QMessageBox.NoIcon, buttons=QtWidgets.QMessageBox.Ok, autostart=True):
        super(Alert, self).__init__(None)

        self.common = common

        self.common.log('Alert', '__init__')

        self.setWindowTitle("OnionShare")
        self.setWindowIcon(QtGui.QIcon(self.common.get_resource_path('images/logo.png')))
        self.setText(message)
        self.setIcon(icon)
        self.setStandardButtons(buttons)

        if autostart:
            self.exec_()


class AddFileDialog(QtWidgets.QFileDialog):
    """
    Overridden version of QFileDialog which allows us to select folders as well
    as, or instead of, files. For adding files/folders to share.

    Note that this dialog can't be used in macOS, only in Windows, Linux, and BSD.
    This is because the macOS sandbox requires native dialogs, and this is a Qt5
    dialog.
    """
    def __init__(self, common, *args, **kwargs):
        QtWidgets.QFileDialog.__init__(self, *args, **kwargs)

        self.common = common
        self.common.log('AddFileDialog', '__init__')

        self.setOption(self.DontUseNativeDialog, True)
        self.setOption(self.ReadOnly, True)
        self.setOption(self.ShowDirsOnly, False)
        self.setFileMode(self.ExistingFiles)
        tree_view = self.findChild(QtWidgets.QTreeView)
        tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        list_view = self.findChild(QtWidgets.QListView, "listView")
        list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def accept(self):
        self.common.log('AddFileDialog', 'accept')
        QtWidgets.QDialog.accept(self)
