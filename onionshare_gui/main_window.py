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
from onionshare.web import Web

from .tor_connection_dialog import TorConnectionDialog
from .settings_dialog import SettingsDialog
from .widgets import Alert
from .update_checker import UpdateThread
from .tab_widget import TabWidget


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
        self.setWindowIcon(
            QtGui.QIcon(self.common.get_resource_path("images/logo.png"))
        )

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
                QtGui.QIcon(self.common.get_resource_path("images/logo_grayscale.png"))
            )
        else:
            self.system_tray.setIcon(
                QtGui.QIcon(self.common.get_resource_path("images/logo.png"))
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
            self.common.get_resource_path("images/server_stopped.png")
        )
        self.status_bar.server_status_image_working = QtGui.QImage(
            self.common.get_resource_path("images/server_working.png")
        )
        self.status_bar.server_status_image_started = QtGui.QImage(
            self.common.get_resource_path("images/server_started.png")
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
            QtGui.QIcon(self.common.get_resource_path("images/settings.png"))
        )
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet(self.common.gui.css["settings_button"])
        self.status_bar.addPermanentWidget(self.settings_button)

        # Tabs
        self.tabs = TabWidget(self.common, self.system_tray, self.status_bar)

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

        # After connecting to Tor, check for updates
        self.check_for_updates()

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

        def reload_settings():
            self.common.log(
                "OnionShareGui", "open_settings", "settings have changed, reloading"
            )
            self.common.settings.load()

            # We might've stopped the main requests timer if a Tor connection failed.
            # If we've reloaded settings, we probably succeeded in obtaining a new
            # connection. If so, restart the timer.
            if not self.common.gui.local_only:
                if self.common.gui.onion.is_authenticated():
                    if not self.timer.isActive():
                        self.timer.start(500)
                    self.share_mode.on_reload_settings()
                    self.receive_mode.on_reload_settings()
                    self.website_mode.on_reload_settings()
                    self.status_bar.clearMessage()

            # If we switched off the auto-stop timer setting, ensure the widget is hidden.
            if not self.common.settings.get("autostop_timer"):
                self.share_mode.server_status.autostop_timer_container.hide()
                self.receive_mode.server_status.autostop_timer_container.hide()
                self.website_mode.server_status.autostop_timer_container.hide()
            # If we switched off the auto-start timer setting, ensure the widget is hidden.
            if not self.common.settings.get("autostart_timer"):
                self.share_mode.server_status.autostart_timer_datetime = None
                self.receive_mode.server_status.autostart_timer_datetime = None
                self.website_mode.server_status.autostart_timer_datetime = None
                self.share_mode.server_status.autostart_timer_container.hide()
                self.receive_mode.server_status.autostart_timer_container.hide()
                self.website_mode.server_status.autostart_timer_container.hide()

        d = SettingsDialog(self.common)
        # d.settings_saved.connect(reload_settings)
        # TODO: move the reload_settings logic into tabs
        d.exec_()

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

                self.update_thread = UpdateThread(
                    self.common, self.common.gui.onion, self.common.gui.config
                )
                self.update_thread.update_available.connect(update_available)
                self.update_thread.start()

    def closeEvent(self, e):
        self.common.log("MainWindow", "closeEvent")

        if self.tabs.are_tabs_active():
            # Open the warning dialog
            dialog = QtWidgets.QMessageBox()
            dialog.setWindowTitle(strings._("gui_quit_warning_title"))
            dialog.setText(strings._("gui_quit_warning_description"))
            dialog.setIcon(QtWidgets.QMessageBox.Critical)
            dialog.addButton(
                strings._("gui_quit_warning_quit"), QtWidgets.QMessageBox.YesRole
            )
            cancel_button = dialog.addButton(
                strings._("gui_quit_warning_cancel"), QtWidgets.QMessageBox.NoRole
            )
            dialog.setDefaultButton(cancel_button)
            reply = dialog.exec_()

            # Close
            if reply == 0:
                self.system_tray.hide()
                e.accept()
            # Cancel
            else:
                e.ignore()
            return

        self.system_tray.hide()
        e.accept()

    def cleanup(self):
        self.common.gui.onion.cleanup()
        # TODO: Run the tab's cleanup
