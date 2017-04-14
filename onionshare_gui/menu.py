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
from PyQt5 import QtCore, QtWidgets

from onionshare import strings
from .settings_dialog import SettingsDialog

class Menu(QtWidgets.QMenuBar):
    """
    OnionShare's menu bar.
    """
    def __init__(self, qtapp):
        super(Menu, self).__init__()
        self.qtapp = qtapp

        file_menu = self.addMenu(strings._('gui_menu_file_menu', True))

        settings_action = file_menu.addAction(strings._('gui_menu_settings_action', True))
        settings_action.triggered.connect(self.settings)
        quit_action = file_menu.addAction(strings._('gui_menu_quit_action', True))
        quit_action.triggered.connect(self.quit)

    def settings(self):
        """
        Settings action triggered.
        """
        SettingsDialog(self.qtapp)

    def quit(self):
        """
        Quit action triggered.
        """
        self.parent().qtapp.quit()
