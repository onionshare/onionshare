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
import os
import threading
import time
import queue
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings, common
from onionshare.common import Common, ShutdownTimer
from onionshare.onion import *

from .share_mode import ShareMode
from .receive_mode import ReceiveMode

from .tor_connection_dialog import TorConnectionDialog
from .settings_dialog import SettingsDialog
from .file_selection import FileSelection
from .server_status import ServerStatus
from .downloads import Downloads
from .alert import Alert
from .update_checker import UpdateThread

class OnionShareGui(QtWidgets.QMainWindow):
    """
    OnionShareGui is the main window for the GUI that contains all of the
    GUI elements.
    """
    start_server_finished = QtCore.pyqtSignal()
    stop_server_finished = QtCore.pyqtSignal()
    starting_server_step2 = QtCore.pyqtSignal()
    starting_server_step3 = QtCore.pyqtSignal()
    starting_server_error = QtCore.pyqtSignal(str)

    MODE_SHARE = 'share'
    MODE_RECEIVE = 'receive'

    def __init__(self, common, web, onion, qtapp, app, filenames, config=False, local_only=False):
        super(OnionShareGui, self).__init__()

        self.common = common
        self.common.log('OnionShareGui', '__init__')

        self._initSystemTray()

        self.web = web
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

        # Share and receive mode widgets
        self.receive_mode = ReceiveMode(self.common)
        self.share_mode = ReceiveMode(self.common)

        self.update_mode_switcher()

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

        # Status bar, zip progress bar
        self._zip_progress_bar = None
        # Status bar, sharing messages
        self.server_share_status_label = QtWidgets.QLabel('')
        self.server_share_status_label.setStyleSheet('QLabel { font-style: italic; color: #666666; padding: 2px; }')
        self.status_bar.insertWidget(0, self.server_share_status_label)

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

        # The server isn't active yet
        self.set_server_active(False)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_requests)

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

        self.adjustSize();

    def share_mode_clicked(self):
        self.mode = self.MODE_SHARE
        self.update_mode_switcher()

    def receive_mode_clicked(self):
        self.mode = self.MODE_RECEIVE
        self.update_mode_switcher()

    def _initSystemTray(self):
        menu = QtWidgets.QMenu()
        self.settingsAction = menu.addAction(strings._('gui_settings_window_title', True))
        self.settingsAction.triggered.connect(self.open_settings)
        self.helpAction = menu.addAction(strings._('gui_settings_button_help', True))
        self.helpAction.triggered.connect(SettingsDialog.help_clicked)
        self.exitAction = menu.addAction(strings._('systray_menu_exit', True))
        self.exitAction.triggered.connect(self.close)

        self.systemTray = QtWidgets.QSystemTrayIcon(self)
        # The convention is Mac systray icons are always grayscale
        if self.common.platform == 'Darwin':
            self.systemTray.setIcon(QtGui.QIcon(self.common.get_resource_path('images/logo_grayscale.png')))
        else:
            self.systemTray.setIcon(QtGui.QIcon(self.common.get_resource_path('images/logo.png')))
        self.systemTray.setContextMenu(menu)
        self.systemTray.show()

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
                    # If there were some files listed for sharing, we should be ok to
                    # re-enable the 'Start Sharing' button now.
                    if self.server_status.file_selection.get_num_files() > 0:
                        self.primary_action.show()
                        self.info_widget.show()
                    self.status_bar.clearMessage()
            # If we switched off the shutdown timeout setting, ensure the widget is hidden.
            if not self.common.settings.get('shutdown_timeout'):
                self.server_status.shutdown_timeout_container.hide()

        d = SettingsDialog(self.common, self.onion, self.qtapp, self.config, self.local_only)
        d.settings_saved.connect(reload_settings)
        d.exec_()

        # When settings close, refresh the server status UI
        self.server_status.update()

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

    def check_for_requests(self):
        """
        Check for messages communicated from the web app, and update the GUI accordingly.
        """
        self.update()

        if not self.local_only:
            # Have we lost connection to Tor somehow?
            if not self.onion.is_authenticated():
                self.timer.stop()
                if self.server_status.status != self.server_status.STATUS_STOPPED:
                    self.server_status.stop_server()
                self.primary_action.hide()
                self.info_widget.hide()
                self.status_bar.showMessage(strings._('gui_tor_connection_lost', True))
                if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('gui_tor_connection_lost', True), strings._('gui_tor_connection_error_settings', True))

        # scroll to the bottom of the dl progress bar log pane
        # if a new download has been added
        if self.new_download:
            self.downloads.downloads_container.vbar.setValue(self.downloads.downloads_container.vbar.maximum())
            self.new_download = False

        events = []

        done = False
        while not done:
            try:
                r = self.web.q.get(False)
                events.append(r)
            except queue.Empty:
                done = True

        for event in events:
            if event["type"] == self.web.REQUEST_LOAD:
                self.status_bar.showMessage(strings._('download_page_loaded', True))

            elif event["type"] == self.web.REQUEST_DOWNLOAD:
                self.downloads.no_downloads_label.hide()
                self.downloads.add_download(event["data"]["id"], web.zip_filesize)
                self.new_download = True
                self.downloads_in_progress += 1
                self.update_downloads_in_progress(self.downloads_in_progress)
                if self.systemTray.supportsMessages() and self.common.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('systray_download_started_title', True), strings._('systray_download_started_message', True))

            elif event["type"] == self.web.REQUEST_RATE_LIMIT:
                self.stop_server()
                Alert(self.common, strings._('error_rate_limit'), QtWidgets.QMessageBox.Critical)

            elif event["type"] == self.web.REQUEST_PROGRESS:
                self.downloads.update_download(event["data"]["id"], event["data"]["bytes"])

                # is the download complete?
                if event["data"]["bytes"] == self.web.zip_filesize:
                    if self.systemTray.supportsMessages() and self.common.settings.get('systray_notifications'):
                        self.systemTray.showMessage(strings._('systray_download_completed_title', True), strings._('systray_download_completed_message', True))
                    # Update the total 'completed downloads' info
                    self.downloads_completed += 1
                    self.update_downloads_completed(self.downloads_completed)
                    # Update the 'in progress downloads' info
                    self.downloads_in_progress -= 1
                    self.update_downloads_in_progress(self.downloads_in_progress)

                    # close on finish?
                    if not self.web.stay_open:
                        self.server_status.stop_server()
                        self.status_bar.clearMessage()
                        self.server_share_status_label.setText(strings._('closing_automatically', True))
                else:
                    if self.server_status.status == self.server_status.STATUS_STOPPED:
                        self.downloads.cancel_download(event["data"]["id"])
                        self.downloads_in_progress = 0
                        self.update_downloads_in_progress(self.downloads_in_progress)


            elif event["type"] == self.web.REQUEST_CANCELED:
                self.downloads.cancel_download(event["data"]["id"])
                # Update the 'in progress downloads' info
                self.downloads_in_progress -= 1
                self.update_downloads_in_progress(self.downloads_in_progress)
                if self.systemTray.supportsMessages() and self.common.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('systray_download_canceled_title', True), strings._('systray_download_canceled_message', True))

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('[#{0:d}] {1:s}: {2:s}'.format(self.web.error404_count, strings._('other_page_loaded', True), event["path"]))

        # If the auto-shutdown timer has stopped, stop the server
        if self.server_status.status == self.server_status.STATUS_STARTED:
            if self.app.shutdown_timer and self.common.settings.get('shutdown_timeout'):
                if self.timeout > 0:
                    now = QtCore.QDateTime.currentDateTime()
                    seconds_remaining = now.secsTo(self.server_status.timeout)
                    self.server_status.server_button.setText(strings._('gui_stop_server_shutdown_timeout', True).format(seconds_remaining))
                    if not self.app.shutdown_timer.is_alive():
                        # If there were no attempts to download the share, or all downloads are done, we can stop
                        if self.web.download_count == 0 or self.web.done:
                            self.server_status.stop_server()
                            self.status_bar.clearMessage()
                            self.server_share_status_label.setText(strings._('close_on_timeout', True))
                        # A download is probably still running - hold off on stopping the share
                        else:
                            self.status_bar.clearMessage()
                            self.server_share_status_label.setText(strings._('timeout_download_still_running', True))

    def copy_url(self):
        """
        When the URL gets copied to the clipboard, display this in the status bar.
        """
        self.common.log('OnionShareGui', 'copy_url')
        if self.systemTray.supportsMessages() and self.common.settings.get('systray_notifications'):
            self.systemTray.showMessage(strings._('gui_copied_url_title', True), strings._('gui_copied_url', True))

    def copy_hidservauth(self):
        """
        When the stealth onion service HidServAuth gets copied to the clipboard, display this in the status bar.
        """
        self.common.log('OnionShareGui', 'copy_hidservauth')
        if self.systemTray.supportsMessages() and self.common.settings.get('systray_notifications'):
            self.systemTray.showMessage(strings._('gui_copied_hidservauth_title', True), strings._('gui_copied_hidservauth', True))

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def set_server_active(self, active):
        """
        Disable the Settings button while an OnionShare server is active.
        """
        if active:
            self.settings_button.hide()
        else:
            self.settings_button.show()

        # Disable settings menu action when server is active
        self.settingsAction.setEnabled(not active)

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


class ZipProgressBar(QtWidgets.QProgressBar):
    update_processed_size_signal = QtCore.pyqtSignal(int)

    def __init__(self, total_files_size):
        super(ZipProgressBar, self).__init__()
        self.setMaximumHeight(20)
        self.setMinimumWidth(200)
        self.setValue(0)
        self.setFormat(strings._('zip_progress_bar_format'))
        cssStyleData ="""
        QProgressBar {
            border: 1px solid #4e064f;
            background-color: #ffffff !important;
            text-align: center;
            color: #9b9b9b;
        }

        QProgressBar::chunk {
            border: 0px;
            background-color: #4e064f;
            width: 10px;
        }"""
        self.setStyleSheet(cssStyleData)

        self._total_files_size = total_files_size
        self._processed_size = 0

        self.update_processed_size_signal.connect(self.update_processed_size)

    @property
    def total_files_size(self):
        return self._total_files_size

    @total_files_size.setter
    def total_files_size(self, val):
        self._total_files_size = val

    @property
    def processed_size(self):
        return self._processed_size

    @processed_size.setter
    def processed_size(self, val):
        self.update_processed_size(val)

    def update_processed_size(self, val):
        self._processed_size = val
        if self.processed_size < self.total_files_size:
            self.setValue(int((self.processed_size * 100) / self.total_files_size))
        elif self.total_files_size != 0:
            self.setValue(100)
        else:
            self.setValue(0)


class OnionThread(QtCore.QThread):
    """
    A QThread for starting our Onion Service.
    By using QThread rather than threading.Thread, we are able
    to call quit() or terminate() on the startup if the user
    decided to cancel (in which case do not proceed with obtaining
    the Onion address and starting the web server).
    """
    def __init__(self, common, function, kwargs=None):
        super(OnionThread, self).__init__()

        self.common = common

        self.common.log('OnionThread', '__init__')
        self.function = function
        if not kwargs:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def run(self):
        self.common.log('OnionThread', 'run')

        self.function(**self.kwargs)
