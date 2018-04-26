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
from onionshare.onion import *

from .file_selection import FileSelection
from .downloads import Downloads
from ..mode import Mode
from ..widgets import Alert


class ShareMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """
    def init(self):
        """
        Custom initialization for ReceiveMode.
        """
        # File selection
        self.file_selection = FileSelection(self.common)
        if self.filenames:
            for filename in self.filenames:
                self.file_selection.file_list.add_file(filename)
        
        # Server status
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.file_selection.server_stopped)
        self.server_status.server_canceled.connect(self.update_primary_action)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
        self.file_selection.file_list.files_updated.connect(self.update_primary_action)

        # Filesize warning
        self.filesize_warning = QtWidgets.QLabel()
        self.filesize_warning.setWordWrap(True)
        self.filesize_warning.setStyleSheet('padding: 10px 0; font-weight: bold; color: #333333;')
        self.filesize_warning.hide()

        # Downloads
        self.downloads = Downloads(self.common)
        self.downloads_in_progress = 0
        self.downloads_completed = 0
        self.new_download = False # For scrolling to the bottom of the downloads list

        # Info label along top of screen
        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel()
        self.info_label.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.info_show_downloads = QtWidgets.QToolButton()
        self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_gray.png')))
        self.info_show_downloads.setCheckable(True)
        self.info_show_downloads.toggled.connect(self.downloads_toggled)
        self.info_show_downloads.setToolTip(strings._('gui_downloads_window_tooltip', True))

        self.info_in_progress_downloads_count = QtWidgets.QLabel()
        self.info_in_progress_downloads_count.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.info_completed_downloads_count = QtWidgets.QLabel()
        self.info_completed_downloads_count.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.update_downloads_completed(self.downloads_in_progress)
        self.update_downloads_in_progress(self.downloads_in_progress)

        self.info_layout.addWidget(self.info_label)
        self.info_layout.addStretch()
        self.info_layout.addWidget(self.info_in_progress_downloads_count)
        self.info_layout.addWidget(self.info_completed_downloads_count)
        self.info_layout.addWidget(self.info_show_downloads)

        self.info_widget = QtWidgets.QWidget()
        self.info_widget.setLayout(self.info_layout)
        self.info_widget.hide()

        # Primary action layout
        self.primary_action_layout.addWidget(self.filesize_warning)
        self.primary_action.hide()
        self.update_primary_action()

        # Status bar, zip progress bar
        self._zip_progress_bar = None

        # Layout
        self.layout.insertWidget(1, self.info_widget)
        self.layout.insertLayout(0, self.file_selection)

        # Always start with focus on file selection
        self.file_selection.setFocus()

    def timer_callback(self):
        """
        This method is called regularly on a timer while share mode is active.
        """
        # Scroll to the bottom of the download progress bar log pane if a new download has been added
        if self.new_download:
            self.downloads.downloads_container.vbar.setValue(self.downloads.downloads_container.vbar.maximum())
            self.new_download = False

        # If the auto-shutdown timer has stopped, stop the server
        if self.server_status.status == self.server_status.STATUS_STARTED:
            if self.app.shutdown_timer and self.common.settings.get('shutdown_timeout'):
                if self.timeout > 0:
                    now = QtCore.QDateTime.currentDateTime()
                    seconds_remaining = now.secsTo(self.server_status.timeout)
                    self.server_status.server_button.setText(strings._('gui_share_stop_server_shutdown_timeout', True).format(seconds_remaining))
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

    def handle_tor_broke(self):
        """
        Handle connection from Tor breaking.
        """
        if self.server_status.status != self.server_status.STATUS_STOPPED:
            self.server_status.stop_server()
        self.primary_action.hide()
        self.info_widget.hide()

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        self.status_bar.showMessage(strings._('download_page_loaded', True))

    def handle_request_download(self, event):
        """
        Handle REQUEST_DOWNLOAD event.
        """
        self.downloads.no_downloads_label.hide()
        self.downloads.add_download(event["data"]["id"], self.web.zip_filesize)
        self.new_download = True
        self.downloads_in_progress += 1
        self.update_downloads_in_progress(self.downloads_in_progress)

        self.system_tray.showMessage(strings._('systray_download_started_title', True), strings._('systray_download_started_message', True))

    def handle_request_rate_limit(self, event):
        """
        Handle REQUEST_RATE_LIMIT event.
        """
        self.stop_server()
        Alert(self.common, strings._('error_rate_limit'), QtWidgets.QMessageBox.Critical)

    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        self.downloads.update_download(event["data"]["id"], event["data"]["bytes"])

        # Is the download complete?
        if event["data"]["bytes"] == self.web.zip_filesize:
            self.system_tray.showMessage(strings._('systray_download_completed_title', True), strings._('systray_download_completed_message', True))

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

    def handle_request_canceled(self, event):
        """
        Handle REQUEST_CANCELED event.
        """
        self.downloads.cancel_download(event["data"]["id"])

        # Update the 'in progress downloads' info
        self.downloads_in_progress -= 1
        self.update_downloads_in_progress(self.downloads_in_progress)
        self.system_tray.showMessage(strings._('systray_download_canceled_title', True), strings._('systray_download_canceled_message', True))

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
            self.info_widget.show()

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
            self.info_widget.hide()

        # Resize window
        self.adjustSize()

    def downloads_toggled(self, checked):
        """
        When the 'Show/hide downloads' button is toggled, show or hide the downloads window.
        """
        self.common.log('ShareMode', 'toggle_downloads')
        if checked:
            self.downloads.downloads_container.show()
        else:
            self.downloads.downloads_container.hide()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.update_downloads_completed(0)
        self.update_downloads_in_progress(0)
        self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_gray.png')))
        self.downloads.no_downloads_label.show()
        self.downloads.downloads_container.resize(self.downloads.downloads_container.sizeHint())

    def update_downloads_completed(self, count):
        """
        Update the 'Downloads completed' info widget.
        """
        if count == 0:
            self.info_completed_downloads_image = self.common.get_resource_path('images/download_completed_none.png')
        else:
            self.info_completed_downloads_image = self.common.get_resource_path('images/download_completed.png')
        self.info_completed_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(self.info_completed_downloads_image, count))
        self.info_completed_downloads_count.setToolTip(strings._('info_completed_downloads_tooltip', True).format(count))

    def update_downloads_in_progress(self, count):
        """
        Update the 'Downloads in progress' info widget.
        """
        if count == 0:
            self.info_in_progress_downloads_image = self.common.get_resource_path('images/download_in_progress_none.png')
        else:
            self.info_in_progress_downloads_image = self.common.get_resource_path('images/download_in_progress.png')
            self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_green.png')))
        self.info_in_progress_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(self.info_in_progress_downloads_image, count))
        self.info_in_progress_downloads_count.setToolTip(strings._('info_in_progress_downloads_tooltip', True).format(count))