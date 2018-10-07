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

from .uploads import Uploads
from .info import ReceiveModeInfo
from .. import Mode

class ReceiveMode(Mode):
    """
    Parts of the main window UI for receiving files.
    """
    def init(self):
        """
        Custom initialization for ReceiveMode.
        """
        # Create the Web object
        self.web = Web(self.common, True, 'receive')

        # Server status
        self.server_status.set_mode('receive')
        self.server_status.server_started_finished.connect(self.update_primary_action)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.update_primary_action)

        # Tell server_status about web, then update
        self.server_status.web = self.web
        self.server_status.update()

        # Uploads
        self.uploads = Uploads(self.common)
        self.uploads.hide()
        self.uploads_in_progress = 0
        self.uploads_completed = 0
        self.new_upload = False # For scrolling to the bottom of the uploads list

        # Information about share, and show uploads button
        self.info = ReceiveModeInfo(self.common, self)
        self.info.show_less()

        # Receive mode info
        self.receive_info = QtWidgets.QLabel(strings._('gui_receive_mode_warning', True))
        self.receive_info.setMinimumHeight(80)
        self.receive_info.setWordWrap(True)

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.info)
        self.main_layout.addWidget(self.receive_info)
        self.main_layout.addWidget(self.primary_action)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.min_width_widget)

        # Wrapper layout
        self.wrapper_layout = QtWidgets.QHBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)
        self.wrapper_layout.addWidget(self.uploads)
        self.setLayout(self.wrapper_layout)

    def get_stop_server_shutdown_timeout_text(self):
        """
        Return the string to put on the stop server button, if there's a shutdown timeout
        """
        return strings._('gui_receive_stop_server_shutdown_timeout', True)

    def timeout_finished_should_stop_server(self):
        """
        The shutdown timer expired, should we stop the server? Returns a bool
        """
        # TODO: wait until the final upload is done before stoppign the server?
        return True

    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.receive_mode.upload_count = 0
        self.web.error404_count = 0

        # Hide and reset the uploads if we have previously shared
        self.reset_info_counters()

    def start_server_step2_custom(self):
        """
        Step 2 in starting the server.
        """
        # Continue
        self.starting_server_step3.emit()
        self.start_server_finished.emit()

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()
        self.info.show_less()

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        self.system_tray.showMessage(strings._('systray_page_loaded_title', True), strings._('systray_upload_page_loaded_message', True))

    def handle_request_started(self, event):
        """
        Handle REQUEST_STARTED event.
        """
        self.uploads.add(event["data"]["id"], event["data"]["content_length"])
        self.info.update_indicator(True)
        self.uploads_in_progress += 1
        self.info.update_uploads_in_progress()

        self.system_tray.showMessage(strings._('systray_upload_started_title', True), strings._('systray_upload_started_message', True))

    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        self.uploads.update(event["data"]["id"], event["data"]["progress"])

    def handle_request_close_server(self, event):
        """
        Handle REQUEST_CLOSE_SERVER event.
        """
        self.stop_server()
        self.system_tray.showMessage(strings._('systray_close_server_title', True), strings._('systray_close_server_message', True))

    def handle_request_upload_file_renamed(self, event):
        """
        Handle REQUEST_UPLOAD_FILE_RENAMED event.
        """
        self.uploads.rename(event["data"]["id"], event["data"]["old_filename"], event["data"]["new_filename"])

    def handle_request_upload_finished(self, event):
        """
        Handle REQUEST_UPLOAD_FINISHED event.
        """
        self.uploads.finished(event["data"]["id"])
        # Update the total 'completed uploads' info
        self.uploads_completed += 1
        self.info.update_uploads_completed()
        # Update the 'in progress uploads' info
        self.uploads_in_progress -= 1
        self.info.update_uploads_in_progress()

    def on_reload_settings(self):
        """
        We should be ok to re-enable the 'Start Receive Mode' button now.
        """
        self.primary_action.show()
        self.info.show_more()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.uploads_completed = 0
        self.uploads_in_progress = 0
        self.info.update_uploads_completed()
        self.info.update_uploads_in_progress()
        self.uploads.reset()

    def update_primary_action(self):
        self.common.log('ReceiveMode', 'update_primary_action')

        # Show the info widget when the server is active
        if self.server_status.status == self.server_status.STATUS_STARTED:
            self.info.show_more()
        else:
            self.info.show_less()

        # Resize window
        self.resize_window()

    def resize_window(self):
        min_width = self.common.min_window_width
        if self.uploads.isVisible():
            min_width += 300
        self.adjust_size.emit(min_width)
