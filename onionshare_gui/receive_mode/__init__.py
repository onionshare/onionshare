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
from ..mode import Mode

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
        self.uploads_in_progress = 0
        self.uploads_completed = 0
        self.new_upload = False # For scrolling to the bottom of the uploads list

        # Information about share, and show uploads button
        self.info_in_progress_uploads_count = QtWidgets.QLabel()
        self.info_in_progress_uploads_count.setStyleSheet(self.common.css['mode_info_label'])

        self.info_completed_uploads_count = QtWidgets.QLabel()
        self.info_completed_uploads_count.setStyleSheet(self.common.css['mode_info_label'])

        self.update_uploads_completed()
        self.update_uploads_in_progress()

        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_layout.addStretch()
        self.info_layout.addWidget(self.info_in_progress_uploads_count)
        self.info_layout.addWidget(self.info_completed_uploads_count)

        self.info_widget = QtWidgets.QWidget()
        self.info_widget.setLayout(self.info_layout)
        self.info_widget.hide()

        # Receive mode info
        self.receive_info = QtWidgets.QLabel(strings._('gui_receive_mode_warning', True))
        self.receive_info.setMinimumHeight(80)
        self.receive_info.setWordWrap(True)

        # Layout
        self.layout.insertWidget(0, self.receive_info)
        self.layout.insertWidget(0, self.info_widget)
        self.layout.addStretch()
        self.horizontal_layout_wrapper.addWidget(self.uploads)

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
        self.info_widget.hide()

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
        self.uploads_in_progress += 1
        self.update_uploads_in_progress()

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
        self.update_uploads_completed()
        # Update the 'in progress uploads' info
        self.uploads_in_progress -= 1
        self.update_uploads_in_progress()

    def on_reload_settings(self):
        """
        We should be ok to re-enable the 'Start Receive Mode' button now.
        """
        self.primary_action.show()
        self.info_widget.show()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.uploads_completed = 0
        self.uploads_in_progress = 0
        self.update_uploads_completed()
        self.update_uploads_in_progress()
        self.uploads.reset()

    def update_uploads_completed(self):
        """
        Update the 'Uploads completed' info widget.
        """
        if self.uploads_completed == 0:
            image = self.common.get_resource_path('images/share_completed_none.svg')
        else:
            image = self.common.get_resource_path('images/share_completed.svg')
        self.info_completed_uploads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.uploads_completed))
        self.info_completed_uploads_count.setToolTip(strings._('info_completed_uploads_tooltip', True).format(self.uploads_completed))

    def update_uploads_in_progress(self):
        """
        Update the 'Uploads in progress' info widget.
        """
        if self.uploads_in_progress == 0:
            image = self.common.get_resource_path('images/share_in_progress_none.svg')
        else:
            image = self.common.get_resource_path('images/share_in_progress.svg')
        self.info_in_progress_uploads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.uploads_in_progress))
        self.info_in_progress_uploads_count.setToolTip(strings._('info_in_progress_uploads_tooltip', True).format(self.uploads_in_progress))

    def update_primary_action(self):
        self.common.log('ReceiveMode', 'update_primary_action')

        # Show the info widget when the server is active
        if self.server_status.status == self.server_status.STATUS_STARTED:
            self.info_widget.show()
        else:
            self.info_widget.hide()

        # Resize window
        self.adjustSize()
