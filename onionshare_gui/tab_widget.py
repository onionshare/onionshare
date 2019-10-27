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

from .tab import Tab


class TabWidget(QtWidgets.QTabWidget):
    """
    A custom tab widget, that has a "+" button for adding new tabs
    """

    def __init__(self, common, system_tray, status_bar):
        super(TabWidget, self).__init__()
        self.common = common
        self.common.log("TabWidget", "__init__")

        self.system_tray = system_tray
        self.status_bar = status_bar

        # Definte the new tab button
        self.new_tab_button = QtWidgets.QPushButton("+", parent=self)
        self.new_tab_button.setFlat(True)
        self.new_tab_button.setAutoFillBackground(True)
        self.new_tab_button.setFixedSize(30, 30)
        self.new_tab_button.clicked.connect(self.new_tab_clicked)
        self.new_tab_button.setStyleSheet(self.common.gui.css["tab_bar_new_tab_button"])
        self.new_tab_button.setToolTip(strings._("gui_new_tab_tooltip"))

        # Use a custom tab bar
        tab_bar = TabBar()
        tab_bar.move_new_tab_button.connect(self.move_new_tab_button)
        self.setTabBar(tab_bar)

        # Set up the tab widget
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setUsesScrollButtons(True)

        self.move_new_tab_button()

    def move_new_tab_button(self):
        # Find the width of all tabs
        tabs_width = sum(
            [self.tabBar().tabRect(i).width() for i in range(self.count())]
        )

        # The current positoin of the new tab button
        pos = self.new_tab_button.pos()

        # If there are so many tabs it scrolls, move the button to the left of the scroll buttons
        if tabs_width > self.width():
            pos.setX(self.width() - 61)
        else:
            # Otherwise move the button to the right of the tabs
            pos.setX(self.tabBar().sizeHint().width())

        self.new_tab_button.move(pos)
        self.new_tab_button.raise_()

    def resizeEvent(self, event):
        # Make sure to move new tab button on each resize
        super(TabWidget, self).resizeEvent(event)
        self.move_new_tab_button()

    def new_tab_clicked(self):
        # Add a new tab
        tab = Tab(self.common, self.system_tray, self.status_bar)
        self.addTab(tab, "New Tab")


class TabBar(QtWidgets.QTabBar):
    """
    A custom tab bar
    """

    move_new_tab_button = QtCore.pyqtSignal()

    def __init__(self):
        super(TabBar, self).__init__()

    def tabLayoutChange(self):
        self.move_new_tab_button.emit()
