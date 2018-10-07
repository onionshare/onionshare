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


class ToggleHistory(QtWidgets.QPushButton):
    """
    Widget for toggling download/upload history on or off, as well as keeping track
    of the indicator counter
    """
    def __init__(self, common, current_mode, history_widget, icon, selected_icon):
        super(ToggleHistory, self).__init__()
        self.common = common
        self.current_mode = current_mode
        self.history_widget = history_widget
        self.icon = icon
        self.selected_icon = selected_icon

        # Toggle button
        self.setDefault(False)
        self.setFixedWidth(35)
        self.setFixedHeight(30)
        self.setFlat(True)
        self.setIcon(icon)
        self.clicked.connect(self.toggle_clicked)

        # Keep track of indicator
        self.indicator_count = 0
        self.indicator_label = QtWidgets.QLabel(parent=self)
        self.indicator_label.setStyleSheet(self.common.css['download_uploads_indicator'])
        self.update_indicator()

    def update_indicator(self, increment=False):
        """
        Update the display of the indicator count. If increment is True, then
        only increment the counter if Downloads is hidden.
        """
        if increment and not self.history_widget.isVisible():
            self.indicator_count += 1

        self.indicator_label.setText("{}".format(self.indicator_count))

        if self.indicator_count == 0:
            self.indicator_label.hide()
        else:
            size = self.indicator_label.sizeHint()
            self.indicator_label.setGeometry(35-size.width(), 0, size.width(), size.height())
            self.indicator_label.show()

    def toggle_clicked(self):
        """
        Toggle showing and hiding the history widget
        """
        self.common.log('ToggleHistory', 'toggle_clicked')

        if self.history_widget.isVisible():
            self.history_widget.hide()
            self.setIcon(self.icon)
            self.setFlat(True)
        else:
            self.history_widget.show()
            self.setIcon(self.selected_icon)
            self.setFlat(False)

        # Reset the indicator count
        self.indicator_count = 0
        self.update_indicator()

        self.current_mode.resize_window()
