# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
from PySide2 import QtCore, QtWidgets, QtGui

from . import strings
from .tor_connection_dialog import TorConnectionDialog
from .settings_dialog import SettingsDialog
from .widgets import Alert
from .update_checker import UpdateThread
from .tab_widget import TabWidget
from .gui_common import GuiCommon
from .threads import OnionCleanupThread


class MainWindow(QtWidgets.QMainWindow):
    """
    MainWindow is the OnionShare main window, which contains the GUI elements, including all open tabs
    """

    def __init__(self, common, filenames):
        super(MainWindow, self).__init__()

        self.common = common
        self.common.log("MainWindow", "__init__")

        # Initialize the window
        self.setMinimumWidth(1040)
        self.setMinimumHeight(700)
        self.setWindowTitle("OnionShare")
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))

        # System tray
        menu = QtWidgets.QMenu()
        self.settings_action = menu.addAction(strings._("gui_settings_window_title"))
        self.settings_action.triggered.connect(self.open_settings)
        self.help_action = menu.addAction(strings._("gui_settings_button_help"))
        self.help_action.triggered.connect(lambda: SettingsDialog.help_clicked(self))
        exit_action = menu.addAction(strings._("systray_menu_exit"))
        exit_action.triggered.connect(self.close)

        self.system_tray = QtWidgets.QSystemTrayIcon(self)

        # The convention is Mac systray icons are always grayscale
        if self.common.platform == "Darwin":
            self.system_tray.setIcon(
                QtGui.QIcon(GuiCommon.get_resource_path("images/logo_grayscale.png"))
            )
        else:
            self.system_tray.setIcon(
                QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png"))
            )
        self.system_tray.setContextMenu(menu)
        self.system_tray.show()

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet(self.common.gui.css["status_bar"])
        self.setStatusBar(self.status_bar)

        # Server status indicator icons
        self.status_bar.server_status_image_stopped = QtGui.QImage(
            GuiCommon.get_resource_path("images/server_stopped.png")
        )
        self.status_bar.server_status_image_working = QtGui.QImage(
            GuiCommon.get_resource_path("images/server_working.png")
        )
        self.status_bar.server_status_image_started = QtGui.QImage(
            GuiCommon.get_resource_path("images/server_started.png")
        )

        # Server status indicator on the status bar
        self.status_bar.server_status_image_label = QtWidgets.QLabel()
        self.status_bar.server_status_image_label.setFixedWidth(20)
        self.status_bar.server_status_label = QtWidgets.QLabel("")
        self.status_bar.server_status_label.setStyleSheet(
            self.common.gui.css["server_status_indicator_label"]
        )
        server_status_indicator_layout = QtWidgets.QHBoxLayout()
        server_status_indicator_layout.addWidget(
            self.status_bar.server_status_image_label
        )
        server_status_indicator_layout.addWidget(self.status_bar.server_status_label)
        self.status_bar.server_status_indicator = QtWidgets.QWidget()
        self.status_bar.server_status_indicator.setLayout(
            server_status_indicator_layout
        )
        self.status_bar.addPermanentWidget(self.status_bar.server_status_indicator)

        # Settings button
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setDefault(False)
        self.settings_button.setFixedSize(40, 50)
        self.settings_button.setIcon(
            QtGui.QIcon(
                GuiCommon.get_resource_path(
                    "images/{}_settings.png".format(self.common.gui.color_mode)
                )
            )
        )
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet(self.common.gui.css["settings_button"])
        self.status_bar.addPermanentWidget(self.settings_button)

        # Tabs
        self.tabs = TabWidget(self.common, self.system_tray, self.status_bar)
        self.tabs.bring_to_front.connect(self.bring_to_front)

        # If we have saved persistent tabs, try opening those
        if len(self.common.settings.get("persistent_tabs")) > 0:
            for mode_settings_id in self.common.settings.get("persistent_tabs"):
                self.tabs.load_tab(mode_settings_id)
        else:
            # Start with opening the first tab
            self.tabs.new_tab_clicked()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.show()

        # Start the "Connecting to Tor" dialog, which calls onion.connect()
        tor_con = TorConnectionDialog(self.common)
        tor_con.canceled.connect(self.tor_connection_canceled)
        tor_con.open_settings.connect(self.tor_connection_open_settings)
        if not self.common.gui.local_only:
            tor_con.start()
            self.settings_have_changed()

        # After connecting to Tor, check for updates
        self.check_for_updates()

        # Create the close warning dialog -- the dialog widget needs to be in the constructor
        # in order to test it
        self.close_dialog = QtWidgets.QMessageBox()
        self.close_dialog.setWindowTitle(strings._("gui_quit_warning_title"))
        self.close_dialog.setText(strings._("gui_quit_warning_description"))
        self.close_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.close_dialog.accept_button = self.close_dialog.addButton(
            strings._("gui_quit_warning_quit"), QtWidgets.QMessageBox.AcceptRole
        )
        self.close_dialog.reject_button = self.close_dialog.addButton(
            strings._("gui_quit_warning_cancel"), QtWidgets.QMessageBox.NoRole
        )
        self.close_dialog.setDefaultButton(self.close_dialog.reject_button)

    def tor_connection_canceled(self):
        """
        If the user cancels before Tor finishes connecting, ask if they want to
        quit, or open settings.
        """
        self.common.log("MainWindow", "tor_connection_canceled")

        def ask():
            a = Alert(
                self.common,
                strings._("gui_tor_connection_ask"),
                QtWidgets.QMessageBox.Question,
                buttons=QtWidgets.QMessageBox.NoButton,
                autostart=False,
            )
            settings_button = QtWidgets.QPushButton(
                strings._("gui_tor_connection_ask_open_settings")
            )
            quit_button = QtWidgets.QPushButton(
                strings._("gui_tor_connection_ask_quit")
            )
            a.addButton(settings_button, QtWidgets.QMessageBox.AcceptRole)
            a.addButton(quit_button, QtWidgets.QMessageBox.RejectRole)
            a.setDefaultButton(settings_button)
            a.exec_()

            if a.clickedButton() == settings_button:
                # Open settings
                self.common.log(
                    "OnionShareGui",
                    "_tor_connection_canceled",
                    "Settings button clicked",
                )
                self.open_settings()

            if a.clickedButton() == quit_button:
                # Quit
                self.common.log(
                    "OnionShareGui", "_tor_connection_canceled", "Quit button clicked"
                )

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.common.gui.qtapp.quit)

        # Wait 100ms before asking
        QtCore.QTimer.singleShot(100, ask)

    def tor_connection_open_settings(self):
        """
        The TorConnectionDialog wants to open the Settings dialog
        """
        self.common.log("MainWindow", "tor_connection_open_settings")

        # Wait 1ms for the event loop to finish closing the TorConnectionDialog
        QtCore.QTimer.singleShot(1, self.open_settings)

    def open_settings(self):
        """
        Open the SettingsDialog.
        """
        self.common.log("MainWindow", "open_settings")
        d = SettingsDialog(self.common)
        d.settings_saved.connect(self.settings_have_changed)
        d.exec_()

    def settings_have_changed(self):
        self.common.log("OnionShareGui", "settings_have_changed")

        if self.common.gui.onion.is_authenticated():
            self.status_bar.clearMessage()

        # Tell each tab that settings have changed
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)
            tab.settings_have_changed()

    def check_for_updates(self):
        """
        Check for updates in a new thread, if enabled.
        """
        if self.common.platform == "Windows" or self.common.platform == "Darwin":
            if self.common.settings.get("use_autoupdate"):

                def update_available(update_url, installed_version, latest_version):
                    Alert(
                        self.common,
                        strings._("update_available").format(
                            update_url, installed_version, latest_version
                        ),
                    )

                self.update_thread = UpdateThread(self.common, self.common.gui.onion)
                self.update_thread.update_available.connect(update_available)
                self.update_thread.start()

    def bring_to_front(self):
        self.common.log("MainWindow", "bring_to_front")
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        self.common.log("MainWindow", "closeEvent")

        if self.tabs.are_tabs_active():
            # Open the warning dialog
            self.common.log("MainWindow", "closeEvent, opening warning dialog")
            self.close_dialog.exec_()

            # Close
            if self.close_dialog.clickedButton() == self.close_dialog.accept_button:
                self.system_tray.hide()
                e.accept()
            # Cancel
            else:
                e.ignore()
            return

        self.system_tray.hide()
        e.accept()

    def event(self, event):
        # Check if color mode switched while onionshare was open, if so, ask user to restart
        if event.type() == QtCore.QEvent.Type.ApplicationPaletteChange:
            QtCore.QTimer.singleShot(1, self.color_mode_warning)
            return True
        return QtWidgets.QMainWindow.event(self, event)

    def color_mode_warning(self):
        """
        Open the color mode warning alert.
        """
        notice = strings._("gui_color_mode_changed_notice")
        Alert(self.common, notice, QtWidgets.QMessageBox.Information)

    def cleanup(self):
        self.common.log("MainWindow", "cleanup")
        self.tabs.cleanup()

        alert = Alert(
            self.common,
            strings._("gui_rendezvous_cleanup"),
            QtWidgets.QMessageBox.Information,
            buttons=QtWidgets.QMessageBox.NoButton,
            autostart=False,
        )
        quit_early_button = QtWidgets.QPushButton(
            strings._("gui_rendezvous_cleanup_quit_early")
        )
        alert.addButton(quit_early_button, QtWidgets.QMessageBox.RejectRole)

        self.onion_cleanup_thread = OnionCleanupThread(self.common)
        self.onion_cleanup_thread.finished.connect(alert.accept)
        self.onion_cleanup_thread.start()

        alert.exec_()
        if alert.clickedButton() == quit_early_button:
            self.common.log("MainWindow", "cleanup", "quitting early")
            if self.onion_cleanup_thread.isRunning():
                self.onion_cleanup_thread.terminate()
                self.onion_cleanup_thread.wait()
            self.common.gui.onion.cleanup(wait=False)

        # Wait 1 second for threads to close gracefully, so tests finally pass
        time.sleep(1)
