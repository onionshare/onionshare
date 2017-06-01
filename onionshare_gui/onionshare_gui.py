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

    def __init__(self, onion, qtapp, app, filenames):
        super(OnionShareGui, self).__init__()

        self._initSystemTray()

        common.log('OnionShareGui', '__init__')

        self.onion = onion
        self.qtapp = qtapp
        self.app = app

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(QtGui.QIcon(common.get_resource_path('images/logo.png')))

        # Load settings
        self.settings = Settings()
        self.settings.load()

        # File selection
        self.file_selection = FileSelection()
        if filenames:
            for filename in filenames:
                self.file_selection.file_list.add_file(filename)

        # Server status
        self.server_status = ServerStatus(self.qtapp, self.app, web, self.file_selection)
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.stop_server)
        self.start_server_finished.connect(self.clear_message)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
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

        # Main layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.file_selection)
        self.layout.addLayout(self.server_status)
        self.layout.addWidget(self.filesize_warning)
        self.layout.addWidget(self.downloads_container)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.show()

        # Check for requests frequently
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_requests)
        self.timer.start(500)

        # Always start with focus on file selection
        self.file_selection.setFocus()

        # The server isn't active yet
        self.set_server_active(False)

        # Start the "Connecting to Tor" dialog, which calls onion.connect()
        tor_con = TorConnectionDialog(self.qtapp, self.settings, self.onion)
        tor_con.canceled.connect(self._tor_connection_canceled)
        tor_con.open_settings.connect(self._tor_connection_open_settings)
        tor_con.start()

        # After connecting to Tor, check for updates
        self.check_for_updates()

    def _initSystemTray(self):
        system = common.get_platform()

        menu = QtWidgets.QMenu()
        settingsAction = menu.addAction(strings._('gui_settings_window_title', True))
        settingsAction.triggered.connect(self.open_settings)
        helpAction = menu.addAction(strings._('gui_settings_button_help', True))
        helpAction.triggered.connect(SettingsDialog.help_clicked)
        exitAction = menu.addAction(strings._('systray_menu_exit', True))
        exitAction.triggered.connect(self.close)

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

        d = SettingsDialog(self.onion, self.qtapp)
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

        # Reset web counters
        web.download_count = 0
        web.error404_count = 0
        web.set_gui_mode()

        # start the onion service in a new thread
        def start_onion_service(self):
            try:
                self.app.start_onion_service()
                self.starting_server_step2.emit()

            except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorTimeout) as e:
                self.starting_server_error.emit(e.args[0])
                return


            self.app.stay_open = not self.settings.get('close_after_first_download')

            # start onionshare http service in new thread
            t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open))
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

        # Refresh the file list in case it has been modified since last share
        self.file_selection.file_list.update()

        # add progress bar to the status bar, indicating the crunching of files.
        self._zip_progress_bar = ZipProgressBar(0)
        self._zip_progress_bar.total_files_size = OnionShareGui._compute_total_size(
            self.file_selection.file_list.filenames)
        self.status_bar.clearMessage()
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            def _set_processed_size(x):
                if self._zip_progress_bar != None:
                    self._zip_progress_bar.update_processed_size_signal.emit(x)
            web.set_file_info(self.file_selection.file_list.filenames, processed_size_callback=_set_processed_size)
            self.app.cleanup_filenames.append(web.zip_filename)
            self.starting_server_step3.emit()

            # done
            self.start_server_finished.emit()

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

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        common.log('OnionShareGui', 'start_server_error')

        self.set_server_active(False)

        Alert(error, QtWidgets.QMessageBox.Warning)
        self.server_status.stop_server()
        self.status_bar.clearMessage()

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        common.log('OnionShareGui', 'stop_server')

        if self.server_status.status != self.server_status.STATUS_STOPPED:
            web.stop(self.app.port)
        self.app.cleanup()
        self.filesize_warning.hide()
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

                self.update_thread = UpdateThread(self.onion)
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
        # scroll to the bottom of the dl progress bar log pane
        # if a new download has been added
        if self.new_download:
            self.vbar.setValue(self.vbar.maximum())
            self.new_download = False
        # only check for requests if the server is running
        if self.server_status.status != self.server_status.STATUS_STARTED:
            return

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

            elif event["type"] == web.REQUEST_CANCELED:
                self.downloads.cancel_download(event["data"]["id"])
                if self.systemTray.supportsMessages() and self.settings.get('systray_notifications'):
                    self.systemTray.showMessage(strings._('systray_download_canceled_title', True), strings._('systray_download_canceled_message', True))

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('[#{0:d}] {1:s}: {2:s}'.format(web.error404_count, strings._('other_page_loaded', True), event["path"]))

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

    def closeEvent(self, e):
        common.log('OnionShareGui', 'closeEvent')
        try:
            if self.server_status.status != self.server_status.STATUS_STOPPED:
                dialog = QtWidgets.QMessageBox()
                dialog.setWindowTitle("OnionShare")
                dialog.setText(strings._('gui_quit_warning', True))
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
            background-color: rgba(255, 255, 255, 0.0) !important;
            border: 0px;
            text-align: center;
        }

        QProgressBar::chunk {
            border: 0px;
            background: qlineargradient(x1: 0.5, y1: 0, x2: 0.5, y2: 1, stop: 0 #b366ff, stop: 1 #d9b3ff);
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
