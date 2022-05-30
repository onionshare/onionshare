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
from .settings_parent_tab import SettingsParentTab
from .connection_tab import AutoConnectTab


class TabWidget(QtWidgets.QTabWidget):
    """
    A custom tab widget, that has a "+" button for adding new tabs
    """

    bring_to_front = QtCore.Signal()

    def __init__(self, common, system_tray, status_bar, window):
        super(TabWidget, self).__init__()
        self.common = common
        self.common.log("TabWidget", "__init__")

        self.system_tray = system_tray
        self.status_bar = status_bar
        self.window = window

        # Keep track of tabs in a dictionary that maps tab_id to tab.
        # Each tab has a unique, auto-incremented id (tab_id). This is different than the
        # tab's index, which changes as tabs are re-arranged.
        self.tabs = {}
        self.current_tab_id = 0  # Each tab has a unique id
        self.tor_settings_tab = None

        # Define the new tab button
        self.new_tab_button = QtWidgets.QPushButton("+", parent=self)
        self.new_tab_button.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_T)
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
                type(self.tabs[tab_id]) is SettingsParentTab
                or type(self.tabs[tab_id]) is AutoConnectTab
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
            type(self.tabs[tab_id]) is SettingsParentTab
            or type(self.tabs[tab_id]) is AutoConnectTab
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
        # if already connected to tor or local only, create a new tab
        # Else open the initial connection tab
        if self.common.gui.local_only or self.common.gui.onion.is_authenticated():
            self.add_tab()
        else:
            self.open_connection_tab()

    def check_autoconnect_tab(self):
        if type(self.tabs[0]) is AutoConnectTab:
            self.tabs[0].check_autoconnect()

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

        sequence = QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_X)
        close_shortcut = QtWidgets.QShortcut(sequence, tab)
        close_shortcut.activated.connect(lambda: self.close_tab(index))

        tab.init(mode_settings)

        # Make sure the title is set
        if tab.get_mode():
            tab.get_mode().mode_settings_widget.title_editing_finished()

        # If it's persistent, set the persistent image in the tab
        self.change_persistent(tab.tab_id, tab.settings.get("persistent", "enabled"))

        # Bring the window to front, in case this is being added by an event
        self.bring_to_front.emit()

    def open_connection_tab(self):
        self.common.log("TabWidget", "open_connection_tab")

        # See if a connection tab is already open, and if so switch to it
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is AutoConnectTab:
                self.setCurrentIndex(self.indexOf(self.tabs[tab_id]))
                return

        connection_tab = AutoConnectTab(
            self.common, self.current_tab_id, self.status_bar, self.window, parent=self
        )
        connection_tab.close_this_tab.connect(self.close_connection_tab)
        connection_tab.tor_is_connected.connect(self.tor_is_connected)
        connection_tab.tor_is_disconnected.connect(self.tor_is_disconnected)
        self.tabs[self.current_tab_id] = connection_tab
        self.current_tab_id += 1
        index = self.addTab(connection_tab, strings._("gui_autoconnect_start"))
        self.setCurrentIndex(index)

    def open_settings_tab(self, from_autoconnect=False, active_tab="general"):
        self.common.log("TabWidget", "open_settings_tab")

        # See if a settings tab is already open, and if so switch to it
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is SettingsParentTab:
                self.setCurrentIndex(self.indexOf(self.tabs[tab_id]))
                return

        settings_tab = SettingsParentTab(
            self.common,
            self.current_tab_id,
            active_tab=active_tab,
            parent=self,
            from_autoconnect=from_autoconnect,
        )
        settings_tab.close_this_tab.connect(self.close_settings_tab)
        sequence = QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_X)
        close_shortcut = QtWidgets.QShortcut(sequence, settings_tab)
        close_shortcut.activated.connect(self.close_settings_tab)
        self.tor_settings_tab = settings_tab.tor_settings_tab
        self.tor_settings_tab.tor_is_connected.connect(self.tor_is_connected)
        self.tor_settings_tab.tor_is_disconnected.connect(self.tor_is_disconnected)
        self.tabs[self.current_tab_id] = settings_tab
        self.current_tab_id += 1
        index = self.addTab(settings_tab, strings._("gui_settings_window_title"))
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
                type(self.tabs[tab_id]) is SettingsParentTab
                or type(self.tabs[tab_id]) is AutoConnectTab
            ):
                tab = self.widget(self.indexOf(self.tabs[tab_id]))
                if tab.settings.get("persistent", "enabled"):
                    persistent_tabs.append(tab.settings.id)
        # Only save if tabs have actually moved
        if persistent_tabs != self.common.settings.get("persistent_tabs"):
            self.common.settings.set("persistent_tabs", persistent_tabs)
            self.common.settings.save()

    def has_no_onionshare_tab(self):
        # Check if the last tab is closed, or there is only one tab
        # which is the settings tab
        return self.count() == 0 or (self.count() == 1 and type(list(self.tabs.values())[0]) is SettingsParentTab)

    def close_tab(self, index):
        self.common.log("TabWidget", "close_tab", f"{index}")
        tab = self.widget(index)
        tab_id = tab.tab_id

        if (
            type(self.tabs[tab_id]) is SettingsParentTab
            or type(self.tabs[tab_id]) is AutoConnectTab
        ):
            self.common.log("TabWidget", "closing a settings tab")

            if type(self.tabs[tab_id]) is SettingsParentTab:
                self.tor_settings_tab = None

            # Remove the tab
            self.removeTab(index)
            del self.tabs[tab.tab_id]

            # If no onionshare feature tab, open a new main window tab
            if self.has_no_onionshare_tab():
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

                # If no onionshare feature tab, open a new main window tab
                if self.has_no_onionshare_tab():
                    self.new_tab_clicked()
            else:
                self.common.log("TabWidget", "user does not want to close the tab")

    def close_connection_tab(self):
        self.common.log("TabWidget", "close_connection_tab")
        for tab_id in self.tabs:
            if type(self.tabs[tab_id]) is AutoConnectTab:
                index = self.indexOf(self.tabs[tab_id])
                self.close_tab(index)
                return

    def close_settings_tab(self):
        self.common.log("TabWidget", "close_settings_tab")
        for tab_id in list(self.tabs):
            if type(self.tabs[tab_id]) is AutoConnectTab:
                # If we are being returned to the AutoConnectTab, but
                # the user has fixed their Tor settings in the TorSettings
                # tab, *and* they have enabled autoconnect, then
                # we should close the AutoConnect Tab.
                if self.common.gui.onion.is_authenticated():
                    self.common.log(
                        "TabWidget",
                        "close_settings_tab",
                        "Tor is connected and we can auto-connect, so closing the tab",
                    )
                    index = self.indexOf(self.tabs[tab_id])
                    self.close_tab(index)
                else:
                    self.tabs[tab_id].reload_settings()
                    self.common.log(
                        "TabWidget",
                        "close_settings_tab",
                        "Reloading settings in case they changed in the TorSettingsTab. Not auto-connecting",
                    )
                break
        # List of indices may have changed due to the above, so we loop over it again as another copy
        for tab_id in list(self.tabs):
            if type(self.tabs[tab_id]) is SettingsParentTab:
                index = self.indexOf(self.tabs[tab_id])
                self.close_tab(index)
                return

    def are_tabs_active(self):
        """
        See if there are active servers in any open tabs
        """
        for tab_id in self.tabs:
            if not (
                type(self.tabs[tab_id]) is SettingsParentTab
                or type(self.tabs[tab_id]) is AutoConnectTab
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
            if not (
                type(self.tabs[tab_id]) is SettingsParentTab
                or type(self.tabs[tab_id]) is AutoConnectTab
            ):
                mode = self.tabs[tab_id].get_mode()
                if mode:
                    mode.tor_connection_started()

    def tor_is_disconnected(self):
        for tab_id in self.tabs:
            if not (
                type(self.tabs[tab_id]) is SettingsParentTab
                or type(self.tabs[tab_id]) is AutoConnectTab
            ):
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
