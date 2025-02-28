# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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

from PySide6 import QtWidgets, QtGui

from ... import strings
from ...gui_common import GuiCommon


class SettingsButton(QtWidgets.QPushButton):
    """
    Widget for toggling showing or hiding the history, as well as keeping track
    of the indicator counter if it's hidden
    """

    def __init__(self, common, tab_widget):
        super(SettingsButton, self).__init__()
        self.common = common
        self.tab_widget = tab_widget

        self.setDefault(False)
        self.setFixedSize(40, 50)
        self.setIcon(
            QtGui.QIcon(
                GuiCommon.get_resource_path(
                    "images/{}_settings.png".format(self.common.gui.color_mode)
                )
            )
        )
        self.setAccessibleName(strings._("gui_settings_window_title"))
        self.clicked.connect(self.open_settings)
        self.setStyleSheet(self.common.gui.css["settings_button"])
        self.setToolTip(strings._("gui_settings_window_title"))

    def open_settings(self):
        self.common.log("SettingsButton", "open settings")
        self.tab_widget.open_settings_tab()
