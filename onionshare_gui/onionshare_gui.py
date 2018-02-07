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
import os, threading, time
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings, common, web
from onionshare.settings import Settings
from onionshare.onion import *

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

    def __init__(self, onion, qtapp, app, filenames, config=False):
        super(OnionShareGui, self).__init__()

        self._initSystemTray()

        common.log('OnionShareGui', '__init__')

        self.onion = onion
        self.qtapp = qtapp
        self.app = app

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.setMinimumWidth(500)

        # Load settings
        self.config = config
        self.settings = Settings(self.config)
        self.settings.load()

        # File selection
        self.file_selection = FileSelection()
        if filenames:
            for filename in filenames:
                self.file_selection.file_list.add_file(filename)

        # Server status
        self.server_status = ServerStatus(self.qtapp, self.app, web, self.file_selection, self.settings)
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.stop_server)
        self.start_server_finished.connect(self.clear_message)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
        self.file_selection.file_list.files_updated.connect(self.update_primary_action)
        self.server_status.url_copied.connect(self.copy_url)
        self.server_status.hidservauth_copied.connect(self.copy_hidservauth)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)

        # Filesize warning
        self.filesize_warning = QtWidgets.QLabel()
        self.filesize_warning.setStyleSheet('padding: 10px 0; font-weight: bold; color: #333333;')
        self.filesize_warning.hide()

        # Downloads
        self.downloads = Downloads()
        self.downloads_container = QtWidgets.QScrollArea()
        self.downloads_container.setWidget(self.downloads)
        self.downloads_container.setWidgetResizable(True)
        self.downloads_container.setMaximumHeight(200)
        self.downloads_container.setMinimumHeight(75)
        self.vbar = self.downloads_container.verticalScrollBar()
        self.downloads_container.hide() # downloads start out hidden
        self.new_download = False

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet(
            "QStatusBar::item { border: 0px; }")
        version_label = QtWidgets.QLabel('v{0:s}'.format(common.get_version()))
        version_label.setStyleSheet('color: #666666')
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setDefault(False)
        self.settings_button.setFlat(True)
        self.settings_button.setIcon( QtGui.QIcon(common.get_resource_path('images/settings.png')) )
        self.settings_button.clicked.connect(self.open_settings)
        self.status_bar.addPermanentWidget(version_label)
        self.status_bar.addPermanentWidget(self.settings_button)
        self.setStatusBar(self.status_bar)

        # Status bar, zip progress bar
        self._zip_progress_bar = None

        # Persistent URL notification
        self.persistent_url_label = QtWidgets.QLabel(strings._('persistent_url_in_use', True))
        self.persistent_url_label.setStyleSheet('font-weight: bold; color: #333333;')
        self.persistent_url_label.hide()

        # Primary action layout
        primary_action_layout = QtWidgets.QVBoxLayout()
        primary_action_layout.addWidget(self.server_status)
        primary_action_layout.addWidget(self.filesize_warning)
        primary_action_layout.addWidget(self.persistent_url_label)
        primary_action_layout.addWidget(self.downloads_container)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(primary_action_layout)
        self.primary_action.hide()
        self.update_primary_action()

        # Main layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.file_selection)
        self.layout.addWidget(self.primary_action)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.show()

        # Always start with focus on file selection
        self.file_selection.setFocus()

        # The server isn't active yet
        self.set_server_active(False)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_requests)

        # Start the "Connecting to Tor" dialog, which calls onion.connect()
        tor_con = TorConnectionDialog(self.qtapp, self.settings, self.onion)
        tor_con.canceled.connect(self._tor_connection_canceled)
        tor_con.open_settings.connect(self._tor_connection_open_settings)
        tor_con.start()

        # Start the timer
        self.timer.start(500)

        # After connecting to Tor, check for updates
        self.check_for_updates()

    def update_primary_action(self):
        # Resize window
        self.resize(self.sizeHint())

        # Show or hide primary action layout
        if self.file_selection.file_list.count() > 0:
            self.primary_action.show()
        else:
            self.primary_action.hide()

    def _initSystemTray(self):
        system = common.get_platform()

        menu = QtWidgets.QMenu()
        self.settingsAction = menu.addAction(strings._('gui_settings_window_title', True))
        self.settingsAction.triggered.connect(self.open_settings)
        self.helpAction = menu.addAction(strings._('gui_settings_button_help', True))
        self.helpAction.triggered.connect(SettingsDialog.help_clicked)
        self.exitAction = menu.addAction(strings._('systray_menu_exit', True))
        self.exitAction.triggered.connect(self.close)

        self.systemTray = QtWidgets.QSystemTrayIcon(self)
        # The convention is Mac systray icons are always grayscale
        if system == 'Darwin':
            self.systemTray.setIcon(QtGui.QIcon(common.get_resource_path('images/logo_grayscale.png')))
        else:
            self.systemTray.setIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))
        self.systemTray.setContextMenu(menu)
        self.systemTray.show()

    def _tor_connection_canceled(self):
        """
        If the user cancels before Tor finishes connecting, ask if they want to
        quit, or open settings.
        """
        common.log('OnionShareGui', '_tor_connection_canceled')

        def ask():
            a = Alert(strings._('gui_tor_connection_ask', True), QtWidgets.QMessageBox.Question, buttons=QtWidgets.QMessageBox.NoButton, autostart=False)
            settings_button = QtWidgets.QPushButton(strings._('gui_tor_connection_ask_open_settings', True))
            quit_button = QtWidgets.QPushButton(strings._('gui_tor_connection_ask_quit', True))
            a.addButton(settings_button, QtWidgets.QMessageBox.AcceptRole)
            a.addButton(quit_button, QtWidgets.QMessageBox.RejectRole)
            a.setDefaultButton(settings_button)
            a.exec_()

            if a.clickedButton() == settings_button:
                # Open settings
                common.log('OnionShareGui', '_tor_connection_canceled', 'Settings button clicked')
                self.open_settings()

            if a.clickedButton() == quit_button:
                # Quit
                common.log('OnionShareGui', '_tor_connection_canceled', 'Quit button clicked')

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.qtapp.quit)

        # Wait 100ms before asking
        QtCore.QTimer.singleShot(100, ask)

    def _tor_connection_open_settings(self):
        """
        The TorConnectionDialog wants to open the Settings dialog
        """
        common.log('OnionShareGui', '_tor_connection_open_settings')

        # Wait 1ms for the event loop to finish closing the TorConnectionDialog
        QtCore.QTimer.singleShot(1, self.open_settings)

    def open_settings(self):
        """
        Open the SettingsDialog.
        """
        common.log('OnionShareGui', 'open_settings')

        def reload_settings():
            common.log('OnionShareGui', 'open_settings', 'settings have changed, reloading')
            self.settings.load()
            # We might've stopped the main requests timer if a Tor connection failed.
            # If we've reloaded settings, we probably succeeded in obtaining a new
            # connection. If so, restart the timer.
            if self.onion.is_authenticated():
                if not self.timer.isActive():
                    self.timer.start(500)
                # If there were some files listed for sharing, we should be ok to
                # re-enable the 'Start Sharing' button now.
                if self.server_status.file_selection.get_num_files() > 0:
                    self.server_status.server_button.setEnabled(True)
                self.status_bar.clearMessage()

        d = SettingsDialog(self.onion, self.qtapp, self.config)
        d.settings_saved.connect(reload_settings)
        d.exec_()

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        common.log('OnionShareGui', 'start_server')

        self.set_server_active(True)

        self.app.set_stealth(self.settings.get('use_stealth'))

        # Hide and reset the downloads if we have previously shared
        self.downloads_container.hide()
        self.downloads.reset_downloads()
        self.status_bar.clearMessage()

        # Reset web counters
        web.download_count = 0
        web.error404_count = 0
        web.set_gui_mode()

        # start the onion service in a new thread
        def start_onion_service(self):
            try:
                self.app.start_onion_service()
                self.starting_server_step2.emit()

            except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorTimeout, OSError) as e:
                self.starting_server_error.emit(e.args[0])
                return


            self.app.stay_open = not self.settings.get('close_after_first_download')

            # start onionshare http service in new thread
            t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open, self.settings.get('slug')))
            t.daemon = True
            t.start()
            # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
            time.sleep(0.2)

        t = threading.Thread(target=start_onion_service, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server. Zipping up files.
        """
        common.log('OnionShareGui', 'start_server_step2')

        # add progress bar to the status bar, indicating the crunching of files.
        self._zip_progress_bar = ZipProgressBar(0)
        self._zip_progress_bar.total_files_size = OnionShareGui._compute_total_size(
            self.file_selection.file_list.filenames)
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            def _set_processed_size(x):
                if self._zip_progress_bar != None:
                    self._zip_progress_bar.update_processed_size_signal.emit(x)
            try:
                web.set_file_info(self.file_selection.file_list.filenames, processed_size_callback=_set_processed_size)
                self.app.cleanup_filenames.append(web.zip_filename)
                self.starting_server_step3.emit()

                # done
                self.start_server_finished.emit()
            except OSError as e:
                self.starting_server_error.emit(e.strerror)
                return

        #self.status_bar.showMessage(strings._('gui_starting_server2', True))
        t = threading.Thread(target=finish_starting_server, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step3(self):
        """
        Step 3 in starting the onionshare server. This displays the large filesize
        warning, if applicable.
        """
        common.log('OnionShareGui', 'start_server_step3')

        # Remove zip progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        # warn about sending large files over Tor
        if web.zip_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

        if self.server_status.timer_enabled:
            # Convert the date value to seconds between now and then
            now = QtCore.QDateTime.currentDateTime()
            self.timeout = now.secsTo(self.server_status.timeout)
            # Set the shutdown timeout value
            if self.timeout > 0:
                self.app.shutdown_timer = common.close_after_seconds(self.timeout)
                self.app.shutdown_timer.start()
            # The timeout has actually already passed since the user clicked Start. Probably the Onion service took too long to start.
            else:
                self.stop_server()
                self.start_server_error(strings._('gui_server_started_after_timeout'))

        if self.settings.get('save_private_key'):
            self.persistent_url_label.show()

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        common.log('OnionShareGui', 'start_server_error')

        self.set_server_active(False)

        Alert(error, QtWidgets.QMessageBox.Warning)
        self.server_status.stop_server()
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None
        self.status_bar.clearMessage()

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        common.log('OnionShareGui', 'stop_server')

        if self.server_status.status != self.server_status.STATUS_STOPPED:
            try:
                web.stop(self.app.port)
            except:
                # Probably we had no port to begin with (Onion service didn't start)
                pass
        self.app.cleanup()
        # Remove ephemeral service, but don't disconnect from Tor
        self.onion.cleanup(stop_tor=False)
        self.filesize_warning.hide()
        self.persistent_url_label.hide()
        self.stop_server_finished.emit()

        self.set_server_active(False)

    def check_for_updates(self):
        """
        Check for updates in a new thread, if enabled.
        """
        system = common.get_platform()
        if system == 'Windows' or system == 'Darwin':
            if self.settings.get('use_autoupdate'):
                def update_available(update_url, installed_version, latest_version):
                    Alert(strings._("update_available", True).format(update_url, installed_version, latest_version))

                self.update_thread = UpdateThread(self.onion, self.config)
                self.update_thread.update_available.connect(update_available)
                self.update_thread.start()

    @staticmethod
    def _compute_total_size(filenames):
        total_size = 0
        for filename in filenames:
            if os.path.isfile(filename):
                total_size += os.path.getsize(filename)
            if os.path.isdir(filename):
                total_size += common.dir_size(filename)
        return total_size

    def check_for_requests(self):
        """
        Check for messages communicated from the web app, and update the GUI accordingly.
        """
        self.update()

        # Have we lost connection to Tor somehow?
        if not self.onion.is_authenticated():
            self.timer.stop()
            if self.server_status.status != self.server_status.STATUS_STOPPED:
                self.server_status.stop_server()
            self.server_status.server_button.setEnabled(False)
            self.status_bar.showMessage(strings._('gui_tor_connection_lost', True))
            if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                self.systemTray.showMessage(strings._('gui_tor_connection_lost', True), strings._('gui_tor_connection_error_settings', True))

        # scroll to the bottom of the dl progress bar log pane
        # if a new download has been added
        if self.new_download:
            self.vbar.setValue(self.vbar.maximum())
            self.new_download = False

        events = []

        done = False
        while not done:
            try:
                r = web.q.get(False)
                events.append(r)
            except web.queue.Empty:
                done = True

        for event in events:
            if event["type"] == web.REQUEST_LOAD:
                self.status_bar.showMessage(strings._('download_page_loaded', True))

            elif event["type"] == web.REQUEST_DOWNLOAD:
                self.downloads_container.show() # show the downloads layout
                self.downloads.add_download(event["data"]["id"], web.zip_filesize)
                self.new_download = True
                if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('systray_download_started_title', True), strings._('systray_download_started_message', True))

            elif event["type"] == web.REQUEST_RATE_LIMIT:
                self.stop_server()
                Alert(strings._('error_rate_limit'), QtWidgets.QMessageBox.Critical)

            elif event["type"] == web.REQUEST_PROGRESS:
                self.downloads.update_download(event["data"]["id"], event["data"]["bytes"])

                # is the download complete?
                if event["data"]["bytes"] == web.zip_filesize:
                    if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                        self.systemTray.showMessage(strings._('systray_download_completed_title', True), strings._('systray_download_completed_message', True))
                    # close on finish?
                    if not web.get_stay_open():
                        self.server_status.stop_server()
                        self.status_bar.showMessage(strings._('closing_automatically', True))
                else:
                    if self.server_status.status == self.server_status.STATUS_STOPPED:
                        self.downloads.cancel_download(event["data"]["id"])

            elif event["type"] == web.REQUEST_CANCELED:
                self.downloads.cancel_download(event["data"]["id"])
                if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('systray_download_canceled_title', True), strings._('systray_download_canceled_message', True))

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('[#{0:d}] {1:s}: {2:s}'.format(web.error404_count, strings._('other_page_loaded', True), event["path"]))

        # If the auto-shutdown timer has stopped, stop the server
        if self.server_status.status == self.server_status.STATUS_STARTED:
            if self.app.shutdown_timer and self.server_status.timer_enabled:
                if self.timeout > 0:
                    if not self.app.shutdown_timer.is_alive():
                        # If there were no attempts to download the share, or all downloads are done, we can stop
                        if web.download_count == 0 or web.done:
                            self.server_status.stop_server()
                            self.status_bar.showMessage(strings._('close_on_timeout', True))
                        # A download is probably still running - hold off on stopping the share
                        else:
                            self.status_bar.showMessage(strings._('timeout_download_still_running', True))

    def copy_url(self):
        """
        When the URL gets copied to the clipboard, display this in the status bar.
        """
        common.log('OnionShareGui', 'copy_url')
        self.status_bar.showMessage(strings._('gui_copied_url', True), 2000)

    def copy_hidservauth(self):
        """
        When the stealth onion service HidServAuth gets copied to the clipboard, display this in the status bar.
        """
        common.log('OnionShareGui', 'copy_hidservauth')
        self.status_bar.showMessage(strings._('gui_copied_hidservauth', True), 2000)

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def set_server_active(self, active):
        """
        Disable the Settings button while an OnionShare server is active.
        """
        self.settings_button.setEnabled(not active)
        if active:
            self.settings_button.setIcon( QtGui.QIcon(common.get_resource_path('images/settings_inactive.png')) )
        else:
            self.settings_button.setIcon( QtGui.QIcon(common.get_resource_path('images/settings.png')) )

        # Disable settings menu action when server is active
        self.settingsAction.setEnabled(not active)

    def closeEvent(self, e):
        common.log('OnionShareGui', 'closeEvent')
        try:
            if self.server_status.status != self.server_status.STATUS_STOPPED:
                common.log('OnionShareGui', 'closeEvent, opening warning dialog')
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
