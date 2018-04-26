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
import queue
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.web import Web

from .share_mode import ShareMode
from .receive_mode import ReceiveMode

from .tor_connection_dialog import TorConnectionDialog
from .settings_dialog import SettingsDialog
from .widgets import Alert
from .update_checker import UpdateThread
from .server_status import ServerStatus

class OnionShareGui(QtWidgets.QMainWindow):
    """
    OnionShareGui is the main window for the GUI that contains all of the
    GUI elements.
    """
    MODE_SHARE = 'share'
    MODE_RECEIVE = 'receive'

    def __init__(self, common, onion, qtapp, app, filenames, config=False, local_only=False):
        super(OnionShareGui, self).__init__()

        self.common = common
        self.common.log('OnionShareGui', '__init__')

        self.onion = onion
        self.qtapp = qtapp
        self.app = app
        self.local_only = local_only

        self.mode = self.MODE_SHARE

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(QtGui.QIcon(self.common.get_resource_path('images/logo.png')))
        self.setMinimumWidth(430)

        # Load settings
        self.config = config
        self.common.load_settings(self.config)

        # System tray
        menu = QtWidgets.QMenu()
        self.settings_action = menu.addAction(strings._('gui_settings_window_title', True))
        self.settings_action.triggered.connect(self.open_settings)
        help_action = menu.addAction(strings._('gui_settings_button_help', True))
        help_action.triggered.connect(SettingsDialog.help_clicked)
        exit_action = menu.addAction(strings._('systray_menu_exit', True))
        exit_action.triggered.connect(self.close)

        self.system_tray = QtWidgets.QSystemTrayIcon(self)
        # The convention is Mac systray icons are always grayscale
        if self.common.platform == 'Darwin':
            self.system_tray.setIcon(QtGui.QIcon(self.common.get_resource_path('images/logo_grayscale.png')))
        else:
            self.system_tray.setIcon(QtGui.QIcon(self.common.get_resource_path('images/logo.png')))
        self.system_tray.setContextMenu(menu)
        self.system_tray.show()

        # Mode switcher, to switch between share files and receive files
        self.mode_switcher_selected_style = """
            QPushButton {
                color: #ffffff;
                background-color: #4e064f;
                border: 0;
                border-right: 1px solid #69266b;
                font-weight: bold;
                border-radius: 0;
            }"""
        self.mode_switcher_unselected_style = """
            QPushButton {
                color: #ffffff;
                background-color: #601f61;
                border: 0;
                font-weight: normal;
                border-radius: 0;
            }"""
        self.share_mode_button = QtWidgets.QPushButton(strings._('gui_mode_share_button', True));
        self.share_mode_button.setFixedHeight(50)
        self.share_mode_button.clicked.connect(self.share_mode_clicked)
        self.receive_mode_button = QtWidgets.QPushButton(strings._('gui_mode_receive_button', True));
        self.receive_mode_button.setFixedHeight(50)
        self.receive_mode_button.clicked.connect(self.receive_mode_clicked)
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setDefault(False)
        self.settings_button.setFixedWidth(40)
        self.settings_button.setFixedHeight(50)
        self.settings_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/settings.png')) )
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #601f61;
                border: 0;
                border-left: 1px solid #69266b;
                border-radius: 0;
            }""")
        mode_switcher_layout = QtWidgets.QHBoxLayout();
        mode_switcher_layout.setSpacing(0)
        mode_switcher_layout.addWidget(self.share_mode_button)
        mode_switcher_layout.addWidget(self.receive_mode_button)
        mode_switcher_layout.addWidget(self.settings_button)

        # Server status indicator on the status bar
        self.server_status_image_stopped = QtGui.QImage(self.common.get_resource_path('images/server_stopped.png'))
        self.server_status_image_working = QtGui.QImage(self.common.get_resource_path('images/server_working.png'))
        self.server_status_image_started = QtGui.QImage(self.common.get_resource_path('images/server_started.png'))
        self.server_status_image_label = QtWidgets.QLabel()
        self.server_status_image_label.setFixedWidth(20)
        self.server_status_label = QtWidgets.QLabel()
        self.server_status_label.setStyleSheet('QLabel { font-style: italic; color: #666666; }')
        server_status_indicator_layout = QtWidgets.QHBoxLayout()
        server_status_indicator_layout.addWidget(self.server_status_image_label)
        server_status_indicator_layout.addWidget(self.server_status_label)
        self.server_status_indicator = QtWidgets.QWidget()
        self.server_status_indicator.setLayout(server_status_indicator_layout)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                font-style: italic;
                color: #666666;
            }

            QStatusBar::item {
                border: 0px;
            }""")
        self.status_bar.addPermanentWidget(self.server_status_indicator)
        self.setStatusBar(self.status_bar)

        # Status bar, sharing messages
        self.server_status_label = QtWidgets.QLabel('')
        self.server_status_label.setStyleSheet('QLabel { font-style: italic; color: #666666; padding: 2px; }')
        self.status_bar.insertWidget(0, self.server_status_label)

        # Share mode
        self.share_mode = ShareMode(self.common, qtapp, app, self.status_bar, self.server_status_label, self.system_tray, filenames)
        self.share_mode.init()
        self.share_mode.server_status.server_started.connect(self.update_server_status_indicator)
        self.share_mode.server_status.server_stopped.connect(self.update_server_status_indicator)
        self.share_mode.start_server_finished.connect(self.update_server_status_indicator)
        self.share_mode.stop_server_finished.connect(self.update_server_status_indicator)
        self.share_mode.stop_server_finished.connect(self.stop_server_finished)
        self.share_mode.start_server_finished.connect(self.clear_message)
        self.share_mode.server_status.button_clicked.connect(self.clear_message)
        self.share_mode.server_status.url_copied.connect(self.copy_url)
        self.share_mode.server_status.hidservauth_copied.connect(self.copy_hidservauth)
        self.share_mode.set_server_active.connect(self.set_server_active)

        # Receive mode
        self.receive_mode = ReceiveMode(self.common, qtapp, app, self.status_bar, self.server_status_label, self.system_tray)
        self.receive_mode.init()
        self.receive_mode.set_server_active.connect(self.set_server_active)

        self.update_mode_switcher()
        self.update_server_status_indicator()

        # Layouts
        contents_layout = QtWidgets.QVBoxLayout()
        contents_layout.setContentsMargins(10, 10, 10, 10)
        contents_layout.addWidget(self.receive_mode)
        contents_layout.addWidget(self.share_mode)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(mode_switcher_layout)
        layout.addLayout(contents_layout)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.show()

        # The servers isn't active yet
        self.set_server_active(False)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_callback)

        # Start the "Connecting to Tor" dialog, which calls onion.connect()
        tor_con = TorConnectionDialog(self.common, self.qtapp, self.onion)
        tor_con.canceled.connect(self._tor_connection_canceled)
        tor_con.open_settings.connect(self._tor_connection_open_settings)
        if not self.local_only:
            tor_con.start()

        # Start the timer
        self.timer.start(500)

        # After connecting to Tor, check for updates
        self.check_for_updates()

    def update_mode_switcher(self):
        # Based on the current mode, switch the mode switcher button styles,
        # and show and hide widgets to switch modes
        if self.mode == self.MODE_SHARE:
            self.share_mode_button.setStyleSheet(self.mode_switcher_selected_style)
            self.receive_mode_button.setStyleSheet(self.mode_switcher_unselected_style)

            self.share_mode.show()
            self.receive_mode.hide()
        else:
            self.share_mode_button.setStyleSheet(self.mode_switcher_unselected_style)
            self.receive_mode_button.setStyleSheet(self.mode_switcher_selected_style)

            self.share_mode.hide()
            self.receive_mode.show()

        self.update_server_status_indicator()
        self.adjustSize();

    def share_mode_clicked(self):
        self.mode = self.MODE_SHARE
        self.update_mode_switcher()

    def receive_mode_clicked(self):
        self.mode = self.MODE_RECEIVE
        self.update_mode_switcher()

    def update_server_status_indicator(self):
        self.common.log('OnionShareGui', 'update_server_status_indicator')

        # Set the status image

        if self.mode == self.MODE_SHARE:
            # Share mode
            if self.share_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_stopped))
                self.server_status_label.setText(strings._('gui_status_indicator_share_stopped', True))
            elif self.share_mode.server_status.status == ServerStatus.STATUS_WORKING:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_working))
                self.server_status_label.setText(strings._('gui_status_indicator_share_working', True))
            elif self.share_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_started))
                self.server_status_label.setText(strings._('gui_status_indicator_share_started', True))
        else:
            # Receive mode
            if self.receive_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_stopped))
                self.server_status_label.setText(strings._('gui_status_indicator_receive_stopped', True))
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_WORKING:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_working))
                self.server_status_label.setText(strings._('gui_status_indicator_receive_working', True))
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_started))
                self.server_status_label.setText(strings._('gui_status_indicator_receive_started', True))

    def stop_server_finished(self):
        # When the server stopped, cleanup the ephemeral onion service
        self.onion.cleanup(stop_tor=False)

    def _tor_connection_canceled(self):
        """
        If the user cancels before Tor finishes connecting, ask if they want to
        quit, or open settings.
        """
        self.common.log('OnionShareGui', '_tor_connection_canceled')

        def ask():
            a = Alert(self.common, strings._('gui_tor_connection_ask', True), QtWidgets.QMessageBox.Question, buttons=QtWidgets.QMessageBox.NoButton, autostart=False)
            settings_button = QtWidgets.QPushButton(strings._('gui_tor_connection_ask_open_settings', True))
            quit_button = QtWidgets.QPushButton(strings._('gui_tor_connection_ask_quit', True))
            a.addButton(settings_button, QtWidgets.QMessageBox.AcceptRole)
            a.addButton(quit_button, QtWidgets.QMessageBox.RejectRole)
            a.setDefaultButton(settings_button)
            a.exec_()

            if a.clickedButton() == settings_button:
                # Open settings
                self.common.log('OnionShareGui', '_tor_connection_canceled', 'Settings button clicked')
                self.open_settings()

            if a.clickedButton() == quit_button:
                # Quit
                self.common.log('OnionShareGui', '_tor_connection_canceled', 'Quit button clicked')

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.qtapp.quit)

        # Wait 100ms before asking
        QtCore.QTimer.singleShot(100, ask)

    def _tor_connection_open_settings(self):
        """
        The TorConnectionDialog wants to open the Settings dialog
        """
        self.common.log('OnionShareGui', '_tor_connection_open_settings')

        # Wait 1ms for the event loop to finish closing the TorConnectionDialog
        QtCore.QTimer.singleShot(1, self.open_settings)

    def open_settings(self):
        """
        Open the SettingsDialog.
        """
        self.common.log('OnionShareGui', 'open_settings')

        def reload_settings():
            self.common.log('OnionShareGui', 'open_settings', 'settings have changed, reloading')
            self.common.settings.load()

            # We might've stopped the main requests timer if a Tor connection failed.
            # If we've reloaded settings, we probably succeeded in obtaining a new
            # connection. If so, restart the timer.
            if not self.local_only:
                if self.onion.is_authenticated():
                    if not self.timer.isActive():
                        self.timer.start(500)
                    self.share_mode.on_reload_settings()
                    self.status_bar.clearMessage()

            # If we switched off the shutdown timeout setting, ensure the widget is hidden.
            if not self.common.settings.get('shutdown_timeout'):
                self.share_mode.server_status.shutdown_timeout_container.hide()

        d = SettingsDialog(self.common, self.onion, self.qtapp, self.config, self.local_only)
        d.settings_saved.connect(reload_settings)
        d.exec_()

        # When settings close, refresh the server status UI
        self.share_mode.server_status.update()

    def check_for_updates(self):
        """
        Check for updates in a new thread, if enabled.
        """
        if self.common.platform == 'Windows' or self.common.platform == 'Darwin':
            if self.common.settings.get('use_autoupdate'):
                def update_available(update_url, installed_version, latest_version):
                    Alert(self.common, strings._("update_available", True).format(update_url, installed_version, latest_version))

                self.update_thread = UpdateThread(self.common, self.onion, self.config)
                self.update_thread.update_available.connect(update_available)
                self.update_thread.start()

    def timer_callback(self):
        """
        Check for messages communicated from the web app, and update the GUI accordingly. Also,
        call ShareMode and ReceiveMode's timer_callbacks.
        """
        self.update()

        if not self.local_only:
            # Have we lost connection to Tor somehow?
            if not self.onion.is_authenticated():
                self.timer.stop()
                self.status_bar.showMessage(strings._('gui_tor_connection_lost', True))
                self.system_tray.showMessage(strings._('gui_tor_connection_lost', True), strings._('gui_tor_connection_error_settings', True))

                self.share_mode.handle_tor_broke()

        # Process events from the web object
        if self.mode == self.MODE_SHARE:
            web = self.share_mode.web
        else:
            web = self.receive_mode.web

        events = []

        done = False
        while not done:
            try:
                r = web.q.get(False)
                events.append(r)
            except queue.Empty:
                done = True

        for event in events:
            if event["type"] == Web.REQUEST_LOAD:
                self.share_mode.handle_request_load(event)

            elif event["type"] == Web.REQUEST_DOWNLOAD:
                self.share_mode.handle_request_download(event)

            elif event["type"] == Web.REQUEST_RATE_LIMIT:
                self.share_mode.handle_request_rate_limit(event)

            elif event["type"] == Web.REQUEST_PROGRESS:
                self.share_mode.handle_request_progress(event)

            elif event["type"] == Web.REQUEST_CANCELED:
                self.share_mode.handle_request_canceled(event)

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('[#{0:d}] {1:s}: {2:s}'.format(web.error404_count, strings._('other_page_loaded', True), event["path"]))

        if self.mode == self.MODE_SHARE:
            self.share_mode.timer_callback()
        else:
            self.receive_mode.timer_callback()

    def copy_url(self):
        """
        When the URL gets copied to the clipboard, display this in the status bar.
        """
        self.common.log('OnionShareGui', 'copy_url')
        self.system_tray.showMessage(strings._('gui_copied_url_title', True), strings._('gui_copied_url', True))

    def copy_hidservauth(self):
        """
        When the stealth onion service HidServAuth gets copied to the clipboard, display this in the status bar.
        """
        self.common.log('OnionShareGui', 'copy_hidservauth')
        self.system_tray.showMessage(strings._('gui_copied_hidservauth_title', True), strings._('gui_copied_hidservauth', True))

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def set_server_active(self, active):
        """
        Disable the Settings and Receive Files buttons while an Share Files server is active.
        """
        if active:
            self.settings_button.hide()
            if self.mode == self.MODE_SHARE:
                self.share_mode_button.show()
                self.receive_mode_button.hide()
            else:
                self.share_mode_button.hide()
                self.receive_mode_button.show()
        else:
            self.settings_button.show()
            self.share_mode_button.show()
            self.receive_mode_button.show()

        # Disable settings menu action when server is active
        self.settings_action.setEnabled(not active)

    def closeEvent(self, e):
        self.common.log('OnionShareGui', 'closeEvent')
        try:
            if self.server_status.status != self.server_status.STATUS_STOPPED:
                self.common.log('OnionShareGui', 'closeEvent, opening warning dialog')
                dialog = QtWidgets.QMessageBox()
                dialog.setWindowTitle(strings._('gui_quit_title', True))
                dialog.setText(strings._('gui_quit_warning', True))
                dialog.setIcon(QtWidgets.QMessageBox.Critical)
                quit_button = dialog.addButton(strings._('gui_quit_warning_quit', True), QtWidgets.QMessageBox.YesRole)
                dont_quit_button = dialog.addButton(strings._('gui_quit_warning_dont_quit', True), QtWidgets.QMessageBox.NoRole)
                dialog.setDefaultButton(dont_quit_button)
                reply = dialog.exec_()

                # Quit
                if reply == 0:
                    self.stop_server()
                    e.accept()
                # Don't Quit
                else:
                    e.ignore()

        except:
            e.accept()
