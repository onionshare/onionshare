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
from .connections import Connections
from .. import Mode
from ..history import History, ToggleHistory, DownloadHistoryItem
from ...widgets import Alert

class WebsiteMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def init(self):
        """
        Custom initialization for WebsiteMode.
        """

        # Create the Web object
        self.web = Web(self.common, True, 'website')

        # File selection
        self.file_selection = FileSelection(self.common, self)
        if self.filenames:
            for filename in self.filenames:
                self.file_selection.file_list.add_file(filename)

        # Server status
        self.server_status.set_mode('website', self.file_selection)
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

        # Connections
        self.connections = Connections(self.common)

        # Connections history
        self.history = History(
            self.common,
            QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/downloads_transparent.png'))),
            strings._('gui_no_publishing'),
            strings._('gui_publishing')
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


    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.error404_count = 0

        # Hide and reset the connections if we have previously shared
        self.reset_info_counters()


    def start_server_step2_custom(self):
        """
        Step 2 in starting the server.
        """
        # Continue
        self.starting_server_step3.emit()
        self.start_server_finished.emit()


    def start_server_step3_custom(self):
        self.filenames = []
        for index in range(self.file_selection.file_list.count()):
            self.filenames.append(self.file_selection.file_list.item(index).filename)

        if self.web.website_mode.set_file_info(self.filenames):
            self.success.emit()
        else:
            # Cancelled
            pass

    def start_server_error_custom(self):
        """
        Start server error.
        """


    def stop_server_custom(self):
        """
        Stop server.
        """
        self.connections_in_progress = 0
        self.filesize_warning.hide()
        self.history.in_progress_count = 0
        self.history.completed_count = 0
        self.history.update_in_progress()
        self.file_selection.file_list.adjustSize()

    def cancel_server_custom(self):
        """
        Stop the compression thread on cancel
        """
        return True

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        self.system_tray.showMessage(strings._('systray_page_loaded_title'), strings._('systray_website_loaded_message'))

    def handle_request_started(self, event):
        """
        Handle REQUEST_STARTED event.
        """
        filesize = self.web.website_mode.download_filesize
        self.connections.add(event["data"]["id"], filesize)
        self.toggle_history.update_indicator(True)
        self.history.in_progress_count += 1
        self.history.update_in_progress()

        self.system_tray.showMessage(strings._('systray_connection_started_title'), strings._('systray_connection_started_message'))


    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        if self.server_status.status == self.server_status.STATUS_STOPPED:
            self.history.in_progress_count  = 0
            self.history.update_in_progress()

    def handle_request_canceled(self, event):
        """
        Handle REQUEST_CANCELED event.
        """
        self.connections.cancel(event["data"]["id"])

        # Update the 'in progress connections' info
        self.history.in_progress_count -= 1
        self.history.update_in_progress()

    def on_reload_settings(self):
        """
        If there were some files listed for sharing, we should be ok to re-enable
        the 'Start Sharing' button now.
        """
        if self.server_status.file_selection.get_num_files() > 0:
            self.primary_action.show()
            self.info_widget.show()

    def update_primary_action(self):
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
                self.info_label.setText(strings._('gui_file_info').format(file_count, total_size_readable))
            else:
                self.info_label.setText(strings._('gui_file_info_single').format(file_count, total_size_readable))

        else:
            self.primary_action.hide()
            self.info_label.hide()


    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.connections.reset()
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
