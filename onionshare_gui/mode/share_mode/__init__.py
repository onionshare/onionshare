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
import os
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.onion import *
from onionshare.common import Common
from onionshare.web import Web

from .file_selection import FileSelection
from .threads import CompressThread
from .. import Mode
from ..history import History, ToggleHistory, DownloadHistoryItem
from ...widgets import Alert


class ShareMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """
    def init(self):
        """
        Custom initialization for ReceiveMode.
        """
        # Threads start out as None
        self.compress_thread = None

        # Create the Web object
        self.web = Web(self.common, True, 'share')

        # File selection
        self.file_selection = FileSelection(self.common)
        if self.filenames:
            for filename in self.filenames:
                self.file_selection.file_list.add_file(filename)

        # Server status
        self.server_status.set_mode('share', self.file_selection)
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.file_selection.server_stopped)
        self.server_status.server_canceled.connect(self.update_primary_action)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
        self.file_selection.file_list.files_updated.connect(self.update_primary_action)
        # Tell server_status about web, then update
        self.server_status.web = self.web
        self.server_status.update()

        # Filesize warning
        self.filesize_warning = QtWidgets.QLabel()
        self.filesize_warning.setWordWrap(True)
        self.filesize_warning.setStyleSheet(self.common.css['share_filesize_warning'])
        self.filesize_warning.hide()

        # Download history
        self.history = History(
            self.common,
            QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/downloads_transparent.png'))),
            strings._('gui_no_downloads'),
            strings._('gui_downloads')
        )
        self.history.hide()

        # Info label
        self.info_label = QtWidgets.QLabel()
        self.info_label.hide()

        # Toggle history
        self.toggle_history = ToggleHistory(
            self.common, self, self.history,
            QtGui.QIcon(self.common.get_resource_path('images/downloads_toggle.png')),
            QtGui.QIcon(self.common.get_resource_path('images/downloads_toggle_selected.png'))
        )

        # Top bar
        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addWidget(self.info_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.toggle_history)

        # Primary action layout
        self.primary_action_layout.addWidget(self.filesize_warning)
        self.primary_action.hide()
        self.update_primary_action()

        # Status bar, zip progress bar
        self._zip_progress_bar = None

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addLayout(self.file_selection)
        self.main_layout.addWidget(self.primary_action)
        self.main_layout.addWidget(self.min_width_widget)

        # Wrapper layout
        self.wrapper_layout = QtWidgets.QHBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)
        self.wrapper_layout.addWidget(self.history)
        self.setLayout(self.wrapper_layout)

        # Always start with focus on file selection
        self.file_selection.setFocus()

    def get_stop_server_shutdown_timeout_text(self):
        """
        Return the string to put on the stop server button, if there's a shutdown timeout
        """
        return strings._('gui_share_stop_server_shutdown_timeout', True)

    def timeout_finished_should_stop_server(self):
        """
        The shutdown timer expired, should we stop the server? Returns a bool
        """
        # If there were no attempts to download the share, or all downloads are done, we can stop
        if self.web.share_mode.download_count == 0 or self.web.done:
            self.server_status.stop_server()
            self.server_status_label.setText(strings._('close_on_timeout', True))
            return True
        # A download is probably still running - hold off on stopping the share
        else:
            self.server_status_label.setText(strings._('timeout_download_still_running', True))
            return False

    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.share_mode.download_count = 0
        self.web.error404_count = 0

        # Hide and reset the downloads if we have previously shared
        self.reset_info_counters()

    def start_server_step2_custom(self):
        """
        Step 2 in starting the server. Zipping up files.
        """
        # Add progress bar to the status bar, indicating the compressing of files.
        self._zip_progress_bar = ZipProgressBar(self.common, 0)
        self.filenames = []
        for index in range(self.file_selection.file_list.count()):
            self.filenames.append(self.file_selection.file_list.item(index).filename)

        self._zip_progress_bar.total_files_size = ShareMode._compute_total_size(self.filenames)
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        self.compress_thread = CompressThread(self)
        self.compress_thread.success.connect(self.starting_server_step3.emit)
        self.compress_thread.success.connect(self.start_server_finished.emit)
        self.compress_thread.error.connect(self.starting_server_error.emit)
        self.server_status.server_canceled.connect(self.compress_thread.cancel)
        self.compress_thread.start()

    def start_server_step3_custom(self):
        """
        Step 3 in starting the server. Remove zip progess bar, and display large filesize
        warning, if applicable.
        """
        # Remove zip progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        # Warn about sending large files over Tor
        if self.web.share_mode.download_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

    def start_server_error_custom(self):
        """
        Start server error.
        """
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

    def stop_server_custom(self):
        """
        Stop server.
        """
        # Remove the progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        self.filesize_warning.hide()
        self.history.in_progress_count = 0
        self.history.completed_count = 0
        self.history.update_in_progress()
        self.file_selection.file_list.adjustSize()

    def cancel_server_custom(self):
        """
        Stop the compression thread on cancel
        """
        if self.compress_thread:
            self.common.log('ShareMode', 'cancel_server: quitting compress thread')
            self.compress_thread.quit()

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()
        self.info_label.hide()

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        self.system_tray.showMessage(strings._('systray_page_loaded_title', True), strings._('systray_download_page_loaded_message', True))

    def handle_request_started(self, event):
        """
        Handle REQUEST_STARTED event.
        """
        if event["data"]["use_gzip"]:
            filesize = self.web.share_mode.gzip_filesize
        else:
            filesize = self.web.share_mode.download_filesize

        item = DownloadHistoryItem(self.common, event["data"]["id"], filesize)
        self.history.add(event["data"]["id"], item)
        self.toggle_history.update_indicator(True)
        self.history.in_progress_count += 1
        self.history.update_in_progress()

        self.system_tray.showMessage(strings._('systray_download_started_title', True), strings._('systray_download_started_message', True))

    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        self.history.update(event["data"]["id"], event["data"]["bytes"])

        # Is the download complete?
        if event["data"]["bytes"] == self.web.share_mode.filesize:
            self.system_tray.showMessage(strings._('systray_download_completed_title', True), strings._('systray_download_completed_message', True))

            # Update completed and in progress labels
            self.history.completed_count += 1
            self.history.in_progress_count -= 1
            self.history.update_completed()
            self.history.update_in_progress()

            # Close on finish?
            if self.common.settings.get('close_after_first_download'):
                self.server_status.stop_server()
                self.status_bar.clearMessage()
                self.server_status_label.setText(strings._('closing_automatically', True))
        else:
            if self.server_status.status == self.server_status.STATUS_STOPPED:
                self.history.cancel(event["data"]["id"])
                self.history.in_progress_count = 0
                self.history.update_in_progress()

    def handle_request_canceled(self, event):
        """
        Handle REQUEST_CANCELED event.
        """
        self.history.cancel(event["data"]["id"])

        # Update in progress count
        self.history.in_progress_count -= 1
        self.history.update_in_progress()
        self.system_tray.showMessage(strings._('systray_download_canceled_title', True), strings._('systray_download_canceled_message', True))

    def on_reload_settings(self):
        """
        If there were some files listed for sharing, we should be ok to re-enable
        the 'Start Sharing' button now.
        """
        if self.server_status.file_selection.get_num_files() > 0:
            self.primary_action.show()
            self.info_label.show()

    def update_primary_action(self):
        self.common.log('ShareMode', 'update_primary_action')

        # Show or hide primary action layout
        file_count = self.file_selection.file_list.count()
        if file_count > 0:
            self.primary_action.show()
            self.info_label.show()

            # Update the file count in the info label
            total_size_bytes = 0
            for index in range(self.file_selection.file_list.count()):
                item = self.file_selection.file_list.item(index)
                total_size_bytes += item.size_bytes
            total_size_readable = self.common.human_readable_filesize(total_size_bytes)

            if file_count > 1:
                self.info_label.setText(strings._('gui_file_info', True).format(file_count, total_size_readable))
            else:
                self.info_label.setText(strings._('gui_file_info_single', True).format(file_count, total_size_readable))

        else:
            self.primary_action.hide()
            self.info_label.hide()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.history.reset()

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

    def __init__(self, common, total_files_size):
        super(ZipProgressBar, self).__init__()
        self.common = common

        self.setMaximumHeight(20)
        self.setMinimumWidth(200)
        self.setValue(0)
        self.setFormat(strings._('zip_progress_bar_format'))
        self.setStyleSheet(self.common.css['share_zip_progess_bar'])

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
