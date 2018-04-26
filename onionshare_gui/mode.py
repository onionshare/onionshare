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
import threading
import time
import os
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.common import Common, ShutdownTimer

from .server_status import ServerStatus
from .onion_thread import OnionThread
from .widgets import Alert

class Mode(QtWidgets.QWidget):
    """
    The class that ShareMode and ReceiveMode inherit from.
    """
    start_server_finished = QtCore.pyqtSignal()
    stop_server_finished = QtCore.pyqtSignal()
    starting_server_step2 = QtCore.pyqtSignal()
    starting_server_step3 = QtCore.pyqtSignal()
    starting_server_error = QtCore.pyqtSignal(str)
    set_share_server_active = QtCore.pyqtSignal(bool)

    def __init__(self, common, qtapp, app, web, status_bar, server_share_status_label, system_tray, filenames=None):
        super(Mode, self).__init__()
        self.common = common
        self.qtapp = qtapp
        self.app = app
        self.web = web

        self.status_bar = status_bar
        self.server_share_status_label = server_share_status_label
        self.system_tray = system_tray

        self.filenames = filenames

        # Server status
        self.server_status = ServerStatus(self.common, self.qtapp, self.app, self.web, False)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.stop_server)
        self.server_status.server_canceled.connect(self.cancel_server)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)

        # Primary action layout
        self.primary_action_layout = QtWidgets.QVBoxLayout()
        self.primary_action_layout.addWidget(self.server_status)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(self.primary_action_layout)

        # Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.primary_action)
        self.setLayout(self.layout)

    def init(self):
        """
        Add custom initialization of the mode here.
        """
        pass

    def timer_callback(self):
        """
        This method is called regularly on a timer.
        """
        pass
    
    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        self.common.log('ShareMode', 'start_server')

        self.set_share_server_active.emit(True)

        self.app.set_stealth(self.common.settings.get('use_stealth'))

        # Hide and reset the downloads if we have previously shared
        self.downloads.reset_downloads()
        self.reset_info_counters()
        self.status_bar.clearMessage()
        self.server_share_status_label.setText('')

        # Reset web counters
        self.web.download_count = 0
        self.web.error404_count = 0

        # start the onion service in a new thread
        def start_onion_service(self):
            try:
                self.app.start_onion_service()
                self.starting_server_step2.emit()

            except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorTimeout, OSError) as e:
                self.starting_server_error.emit(e.args[0])
                return


            self.app.stay_open = not self.common.settings.get('close_after_first_download')

            # start onionshare http service in new thread
            t = threading.Thread(target=self.web.start, args=(self.app.port, self.app.stay_open, self.common.settings.get('slug')))
            t.daemon = True
            t.start()
            # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
            time.sleep(0.2)

        self.common.log('OnionshareGui', 'start_server', 'Starting an onion thread')
        self.t = OnionThread(self.common, function=start_onion_service, kwargs={'self': self})
        self.t.daemon = True
        self.t.start()

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server. Zipping up files.
        """
        self.common.log('ShareMode', 'start_server_step2')

        # add progress bar to the status bar, indicating the compressing of files.
        self._zip_progress_bar = ZipProgressBar(0)
        self.filenames = []
        for index in range(self.file_selection.file_list.count()):
            self.filenames.append(self.file_selection.file_list.item(index).filename)

        self._zip_progress_bar.total_files_size = Mode._compute_total_size(self.filenames)
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            def _set_processed_size(x):
                if self._zip_progress_bar != None:
                    self._zip_progress_bar.update_processed_size_signal.emit(x)
            try:
                self.web.set_file_info(self.filenames, processed_size_callback=_set_processed_size)
                self.app.cleanup_filenames.append(self.web.zip_filename)

                # Only continue if the server hasn't been canceled
                if self.server_status.status != self.server_status.STATUS_STOPPED:
                    self.starting_server_step3.emit()
                    self.start_server_finished.emit()
            except OSError as e:
                self.starting_server_error.emit(e.strerror)
                return

        t = threading.Thread(target=finish_starting_server, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step3(self):
        """
        Step 3 in starting the onionshare server. This displays the large filesize
        warning, if applicable.
        """
        self.common.log('ShareMode', 'start_server_step3')

        # Remove zip progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        # warn about sending large files over Tor
        if self.web.zip_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

        if self.common.settings.get('shutdown_timeout'):
            # Convert the date value to seconds between now and then
            now = QtCore.QDateTime.currentDateTime()
            self.timeout = now.secsTo(self.server_status.timeout)
            # Set the shutdown timeout value
            if self.timeout > 0:
                self.app.shutdown_timer = ShutdownTimer(self.common, self.timeout)
                self.app.shutdown_timer.start()
            # The timeout has actually already passed since the user clicked Start. Probably the Onion service took too long to start.
            else:
                self.stop_server()
                self.start_server_error(strings._('gui_server_started_after_timeout'))

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        self.common.log('ShareMode', 'start_server_error')

        self.set_share_server_active.emit(False)

        Alert(self.common, error, QtWidgets.QMessageBox.Warning)
        self.server_status.stop_server()
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None
        self.status_bar.clearMessage()

    def cancel_server(self):
        """
        Cancel the server while it is preparing to start
        """
        if self.t:
            self.t.quit()
        self.stop_server()

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        self.common.log('ShareMode', 'stop_server')

        if self.server_status.status != self.server_status.STATUS_STOPPED:
            try:
                self.web.stop(self.app.port)
            except:
                # Probably we had no port to begin with (Onion service didn't start)
                pass
        self.app.cleanup()

        # Remove the progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        self.filesize_warning.hide()
        self.downloads_in_progress = 0
        self.downloads_completed = 0
        self.update_downloads_in_progress(0)
        self.file_selection.file_list.adjustSize()

        self.set_share_server_active.emit(False)
        self.stop_server_finished.emit()
    
    @staticmethod
    def _compute_total_size(filenames):
        total_size = 0
        for filename in filenames:
            if os.path.isfile(filename):
                total_size += os.path.getsize(filename)
            if os.path.isdir(filename):
                total_size += Common.dir_size(filename)
        return total_size


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
