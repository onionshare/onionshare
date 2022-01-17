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

from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.mode_settings import ModeSettings

from . import strings
from .tab import Tab
from .threads import EventHandlerThread
from .gui_common import GuiCommon
from .tor_settings_tab import TorSettingsTab
from .settings_tab import SettingsTab


class TabWidget(QtWidgets.QTabWidget):
    """
    A custom tab widget, that has a "+" button for adding new tabs
    """

    bring_to_front = QtCore.Signal()

    def __init__(self, common, system_tray, status_bar):
        super(TabWidget, self).__init__()
        self.common = common
        self.common.log("TabWidget", "__init__")

        self.system_tray = system_tray
        self.status_bar = status_bar

        # Keep track of tabs in a dictionary that maps tab_id to tab.
        # Each tab has a unique, auto-incremented id (tab_id). This is different than the
        # tab's index, which changes as tabs are re-arranged.
        self.tabs = {}
        self.current_tab_id = 0  # Each tab has a unique id
        self.tor_settings_tab = None

        # Define the new tab button
        self.new_tab_button = QtWidgets.QPushButton("+", parent=self)
        self.new_tab_button.setFlat(True)
        self.new_tab_button.setFixedSize(40, 30)
        self.new_tab_button.clicked.connect(self.new_tab_clicked)
        self.new_tab_button.setStyleSheet(
            self.common.gui.css["tab_widget_new_tab_button"]
        )
        self.new_tab_button.setToolTip(strings._("gui_new_tab_tooltip"))

        # Use a custom tab bar
        tab_bar = TabBar()
        tab_bar.move_new_tab_button.connect(self.move_new_tab_button)
        tab_bar.currentChanged.connect(self.tab_changed)
        self.setTabBar(tab_bar)

        # Set up the tab widget
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(True)
        self.setStyleSheet(self.common.gui.css["tab_widget"])

        self.tabCloseRequested.connect(self.close_tab)

        self.move_new_tab_button()

        # Watch the events file for changes
        self.event_handler_t = EventHandlerThread(common)
        self.event_handler_t.new_tab.connect(self.add_tab)
        self.event_handler_t.new_share_tab.connect(self.new_share_tab)
        self.event_handler_t.start()

    def cleanup(self):
        self.common.log("TabWidget", "cleanup")

        # Stop the event thread
        self.event_handler_t.should_quit = True
        self.event_handler_t.quit()
        self.event_handler_t.wait(50)

        # Clean up each tab
        for tab_id in self.tabs:
            if not (
                type(self.tabs[tab_id]) is SettingsTab
                or type(self.tabs[tab_id]) is TorSettingsTab
            ):
                self.tabs[tab_id].cleanup()

    def move_new_tab_button(self):
        # Find the width of all tabs
        tabs_width = sum(
            [self.tabBar().tabRect(i).width() for i in range(self.count())]
        )

        # The current position of the new tab button
        pos = self.new_tab_button.pos()

        # If there are so many tabs it scrolls, move the button to the left of the scroll buttons
        if tabs_width > self.width():
            pos.setX(self.width() - 65)
        else:
            # Otherwise move the button to the right of the tabs
            pos.setX(self.tabBar().sizeHint().width())

        self.new_tab_button.move(pos)
        self.new_tab_button.raise_()

    def tab_changed(self):
        # Active tab was changed
        tab = self.widget(self.currentIndex())
        if not tab:
            self.common.log(
                "TabWidget",
                "tab_changed",
                f"tab at index {self.currentIndex()} does not exist",
            )
            return

        tab_id = tab.tab_id
        self.common.log("TabWidget", "tab_changed", f"Tab was changed to {tab_id}")

        # If it's Settings or Tor Settings, ignore
        if (
            type(self.tabs[tab_id]) is SettingsTab
            or type(self.tabs[tab_id]) is TorSettingsTab
        ):
            # Blank the server status indicator
            self.status_bar.server_status_image_label.clear()
            self.status_bar.server_status_label.clear()
            return

        try:
            mode = self.tabs[tab_id].get_mode()
            if mode:
                # Update the server status indicator to reflect that of the current tab
                self.tabs[tab_id].update_server_status_indicator()
            else:
                # If this tab doesn't have a mode set yet, blank the server status indicator
                self.status_bar.server_status_image_label.clear()
                self.status_bar.server_status_label.clear()
        except KeyError:
            # When all current tabs are closed, index briefly drops to -1 before resetting to 0
            # which will otherwise trigger a KeyError on tab.get_mode() above.
            pass

    def new_tab_clicked(self):
        # Create a new tab
        self.add_tab()

    def load_tab(self, mode_settings_id):
        # Load the tab's mode settings
        mode_settings = ModeSettings(self.common, id=mode_settings_id)
        self.add_tab(mode_settings)

    def new_share_tab(self, filenames):
        mode_settings = ModeSettings(self.common)
        mode_settings.set("persistent", "mode", "share")
        mode_settings.set("share", "filenames", filenames)
        self.add_tab(mode_settings)

    def add_tab(self, mode_settings=None):
        self.common.log("TabWidget", "add_tab", f"mode_settings: {mode_settings}")
        tab = Tab(self.common, self.current_tab_id, self.system_tray, self.status_bar)
        tab.change_title.connect(self.change_title)
        tab.change_icon.connect(self.change_icon)
        tab.change_persistent.connect(self.change_persistent)

        self.tabs[self.current_tab_id] = tab
        self.current_tab_id += 1

        index = self.addTab(tab, strings._("gui_new_tab"))
        self.setCurrentIndex(index)

        tab.init(mode_settings)

        # Make sure the title is set
        if tab.get_mode():
            tab.get_mode().mode_settings_widget.title_editing_finished()

        # If it's persistent, set the persistent image in the tab
        self.change_persistent(tab.tab_id, tab.settings.get("persistent", "enabled"))

        # Bring the window to front, in case this is being added by an event
        self.bring_to_front.emit()

    def open_settings_tab(self):
        self.common.log("TabWidget", "open_settings_tab")

        # See if a settings tab is already open, and if so switch to it
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is SettingsTab:
                self.setCurrentIndex(self.indexOf(self.tabs[tab_id]))
                return

        settings_tab = SettingsTab(self.common, self.current_tab_id)
        settings_tab.close_this_tab.connect(self.close_settings_tab)
        self.tabs[self.current_tab_id] = settings_tab
        self.current_tab_id += 1
        index = self.addTab(settings_tab, strings._("gui_settings_window_title"))
        self.setCurrentIndex(index)

    def open_tor_settings_tab(self):
        self.common.log("TabWidget", "open_tor_settings_tab")

        # See if a settings tab is already open, and if so switch to it
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is TorSettingsTab:
                self.setCurrentIndex(self.indexOf(self.tabs[tab_id]))
                return

        self.tor_settings_tab = TorSettingsTab(
            self.common, self.current_tab_id, self.are_tabs_active(), self.status_bar
        )
        self.tor_settings_tab.close_this_tab.connect(self.close_tor_settings_tab)
        self.tor_settings_tab.tor_is_connected.connect(self.tor_is_connected)
        self.tor_settings_tab.tor_is_disconnected.connect(self.tor_is_disconnected)
        self.tabs[self.current_tab_id] = self.tor_settings_tab
        self.current_tab_id += 1
        index = self.addTab(
            self.tor_settings_tab, strings._("gui_tor_settings_window_title")
        )
        self.setCurrentIndex(index)

    def change_title(self, tab_id, title):
        shortened_title = title
        if len(shortened_title) > 11:
            shortened_title = shortened_title[:10] + "..."

        index = self.indexOf(self.tabs[tab_id])
        self.setTabText(index, shortened_title)
        self.setTabToolTip(index, title)

    def change_icon(self, tab_id, icon_path):
        index = self.indexOf(self.tabs[tab_id])
        self.setTabIcon(index, QtGui.QIcon(GuiCommon.get_resource_path(icon_path)))

        # The icon changes when the server status changes, so if we have an open
        # Tor Settings tab, tell it to update
        if self.tor_settings_tab:
            self.tor_settings_tab.active_tabs_changed(self.are_tabs_active())

    def change_persistent(self, tab_id, is_persistent):
        self.common.log(
            "TabWidget",
            "change_persistent",
            f"tab_id: {tab_id}, is_persistent: {is_persistent}",
        )
        index = self.indexOf(self.tabs[tab_id])
        if is_persistent:
            self.tabBar().setTabButton(
                index,
                QtWidgets.QTabBar.LeftSide,
                self.tabs[tab_id].persistent_image_label,
            )
        else:
            self.tabBar().setTabButton(
                index, QtWidgets.QTabBar.LeftSide, self.tabs[tab_id].invisible_widget
            )

        self.save_persistent_tabs()

    def save_persistent_tabs(self):
        # Figure out the order of persistent tabs to save in settings
        persistent_tabs = []
        for tab_id in self.tabs:
            if not (
                type(self.tabs[tab_id]) is SettingsTab
                or type(self.tabs[tab_id]) is TorSettingsTab
            ):
                tab = self.widget(self.indexOf(self.tabs[tab_id]))
                if tab.settings.get("persistent", "enabled"):
                    persistent_tabs.append(tab.settings.id)
        # Only save if tabs have actually moved
        if persistent_tabs != self.common.settings.get("persistent_tabs"):
            self.common.settings.set("persistent_tabs", persistent_tabs)
            self.common.settings.save()

    def close_tab(self, index):
        self.common.log("TabWidget", "close_tab", f"{index}")
        tab = self.widget(index)
        tab_id = tab.tab_id

        if (
            type(self.tabs[tab_id]) is SettingsTab
            or type(self.tabs[tab_id]) is TorSettingsTab
        ):
            self.common.log("TabWidget", "closing a settings tab")

            if type(self.tabs[tab_id]) is TorSettingsTab:
                self.tor_settings_tab = None

            # Remove the tab
            self.removeTab(index)
            del self.tabs[tab.tab_id]

            # If the last tab is closed, open a new one
            if self.count() == 0:
                self.new_tab_clicked()

        else:
            self.common.log("TabWidget", "closing a service tab")
            if tab.close_tab():
                self.common.log("TabWidget", "user is okay with closing the tab")
                tab.cleanup()

                # If the tab is persistent, delete the settings file from disk
                if tab.settings.get("persistent", "enabled"):
                    tab.settings.delete()

                self.save_persistent_tabs()

                # Remove the tab
                self.removeTab(index)
                del self.tabs[tab.tab_id]

                # If the last tab is closed, open a new one
                if self.count() == 0:
                    self.new_tab_clicked()
            else:
                self.common.log("TabWidget", "user does not want to close the tab")

    def close_settings_tab(self):
        self.common.log("TabWidget", "close_settings_tab")
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is SettingsTab:
                index = self.indexOf(self.tabs[tab_id])
                self.close_tab(index)
                return

    def close_tor_settings_tab(self):
        self.common.log("TabWidget", "close_tor_settings_tab")
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is TorSettingsTab:
                index = self.indexOf(self.tabs[tab_id])
                self.close_tab(index)
                return

    def are_tabs_active(self):
        """
        See if there are active servers in any open tabs
        """
        for tab_id in self.tabs:
            if not (
                type(self.tabs[tab_id]) is SettingsTab
                or type(self.tabs[tab_id]) is TorSettingsTab
            ):
                mode = self.tabs[tab_id].get_mode()
                if mode:
                    if mode.server_status.status != mode.server_status.STATUS_STOPPED:
                        return True
        return False

    def paintEvent(self, event):
        super(TabWidget, self).paintEvent(event)
        # Save the order of persistent tabs whenever a new tab is switched to -- ideally we would
        # do this whenever tabs gets moved, but paintEvent is the only event that seems to get triggered
        # when this happens
        self.save_persistent_tabs()

    def resizeEvent(self, event):
        # Make sure to move new tab button on each resize
        super(TabWidget, self).resizeEvent(event)
        self.move_new_tab_button()

    def tor_is_connected(self):
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is SettingsTab:
                self.tabs[tab_id].tor_is_connected()
            else:
                if not type(self.tabs[tab_id]) is TorSettingsTab:
                    mode = self.tabs[tab_id].get_mode()
                    if mode:
                        mode.tor_connection_started()

    def tor_is_disconnected(self):
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is SettingsTab:
                self.tabs[tab_id].tor_is_disconnected()
            else:
                if not type(self.tabs[tab_id]) is TorSettingsTab:
                    mode = self.tabs[tab_id].get_mode()
                    if mode:
                        mode.tor_connection_stopped()


class TabBar(QtWidgets.QTabBar):
    """
    A custom tab bar
    """

    move_new_tab_button = QtCore.Signal()

    def __init__(self):
        super(TabBar, self).__init__()

    def tabLayoutChange(self):
        self.move_new_tab_button.emit()
