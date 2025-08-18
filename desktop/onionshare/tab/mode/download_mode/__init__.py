# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
import re
import requests

from PySide6 import QtCore, QtWidgets, QtGui

from onionshare_cli.common import Common
from onionshare_cli.web import Web

from urllib.parse import urlparse

from .. import Mode
from ..history import History, ToggleHistory, DownloadHistoryItem
from .... import strings
from ....threads import DownloadThread
from ....widgets import MinimumSizeWidget
from ....gui_common import GuiCommon


class DownloadMode(Mode):
    """
    Parts of the main window UI for downloading a share from another OnionShare.
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def init(self):
        """
        Custom initialization for DownloadMode.
        """

        self.id = 0

        # Download mode is client-only (no web server)
        self.is_server = False
        # Polling sets this to true and prevents the mode from 'stopping'
        self.is_polling = False

        # Download (receive) image
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(
                        "images/{}_mode_receive.png".format(self.common.gui.color_mode)
                    )
                )
            )
        )
        self.image_label.setFixedSize(300, 300)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addStretch()
        image_layout.addWidget(self.image_label)
        image_layout.addStretch()
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # Header
        header_label = QtWidgets.QLabel(strings._("gui_new_tab_download_button"))
        header_label.setWordWrap(True)
        header_label.setStyleSheet(self.common.gui.css["mode_header_label"])

        # Download mode explainer
        self.download_mode_explainer = QtWidgets.QLabel(
            strings._("gui_download_mode_explainer")
        )
        self.download_mode_explainer.setMinimumHeight(80)
        self.download_mode_explainer.setWordWrap(True)

        # OnionShare URL
        self.onionshare_url_label = QtWidgets.QLabel(
            strings._("mode_settings_download_onionshare_url_label")
        )
        self.onionshare_url = QtWidgets.QLineEdit()
        self.onionshare_url.setStyleSheet(
            "QLineEdit { color: black; } QLineEdit::placeholder { color: gray; }"
        )
        self.onionshare_url.setPlaceholderText(
            "http://lldan5gahapx5k7iafb3s4ikijc4ni7gx5iywdflkba5y2ezyg6sjgyd.onion"
        )

        # Does the OnionShare URL use Client Auth?
        self.onionshare_uses_private_key_checkbox = QtWidgets.QCheckBox()
        self.onionshare_uses_private_key_checkbox.setText(
            strings._("mode_settings_download_onionshare_uses_private_key")
        )
        self.onionshare_uses_private_key_checkbox.clicked.connect(
            self.onionshare_uses_private_key_checkbox_checked
        )

        self.onionshare_private_key = QtWidgets.QLineEdit()
        self.onionshare_private_key.setPlaceholderText(
            strings._("mode_settings_download_onionshare_private_key")
        )
        self.onionshare_private_key.setStyleSheet(
            "QLineEdit { color: black; } QLineEdit::placeholder { color: gray; }"
        )
        self.onionshare_private_key.hide()

        onionshare_url_layout = QtWidgets.QVBoxLayout()
        onionshare_url_layout.setContentsMargins(0, 0, 0, 0)
        onionshare_url_layout.addWidget(self.onionshare_url_label)
        onionshare_url_layout.addWidget(self.onionshare_url)
        onionshare_url_layout.addWidget(self.onionshare_uses_private_key_checkbox)
        onionshare_url_layout.addWidget(self.onionshare_private_key)
        self.mode_settings_widget.mode_specific_layout.addLayout(onionshare_url_layout)

        # Polling option
        self.poll_checkbox = QtWidgets.QCheckBox()
        self.poll_checkbox.setText(strings._("mode_settings_download_poll_label"))
        self.poll_checkbox.clicked.connect(self.poll_checkbox_checked)
        self.poll = QtWidgets.QSpinBox()
        self.poll.setRange(0, 525600)
        self.poll.setValue(0)  # Set initial value to 0
        self.poll.setSingleStep(1)  # increment in minutes
        self.poll.valueChanged.connect(self.poll_checkbox_checked)

        self.poll_warning_label = QtWidgets.QLabel(
            strings._("mode_settings_download_poll_warning_label")
        )
        self.poll_warning_label.hide()
        poll_warning_layout = QtWidgets.QHBoxLayout()
        poll_warning_layout.addWidget(self.poll_warning_label)

        poll_settings_layout = QtWidgets.QHBoxLayout()
        poll_settings_layout.addWidget(self.poll_checkbox)
        poll_settings_layout.addWidget(self.poll)

        poll_layout = QtWidgets.QVBoxLayout()
        poll_layout.addLayout(poll_settings_layout)
        poll_layout.addLayout(poll_warning_layout)
        self.mode_settings_widget.mode_specific_layout.addLayout(poll_layout)

        # Data dir
        data_dir_label = QtWidgets.QLabel(
            strings._("mode_settings_receive_data_dir_label")
        )
        self.data_dir_lineedit = QtWidgets.QLineEdit()
        self.data_dir_lineedit.setReadOnly(True)
        self.data_dir_lineedit.setText(self.settings.get("download", "data_dir"))
        data_dir_button = QtWidgets.QPushButton(
            strings._("mode_settings_receive_data_dir_browse_button")
        )
        data_dir_button.clicked.connect(self.data_dir_button_clicked)
        data_dir_layout = QtWidgets.QHBoxLayout()
        data_dir_layout.addWidget(data_dir_label)
        data_dir_layout.addWidget(self.data_dir_lineedit)
        data_dir_layout.addWidget(data_dir_button)
        self.mode_settings_widget.mode_specific_layout.addLayout(data_dir_layout)

        # These settings make no sense for Download mode
        self.mode_settings_widget.persistent_checkbox.hide()
        self.mode_settings_widget.persistent_autostart_on_launch_checkbox.hide()
        self.mode_settings_widget.public_checkbox.hide()
        self.mode_settings_widget.advanced_widget.hide()
        self.mode_settings_widget.toggle_advanced_button.hide()

        # Server status
        self.server_status.set_mode("download")
        self.server_status.server_stopped.connect(self.update_primary_action)

        self.server_status.update()

        # Download history
        self.history = History(
            self.common,
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path("images/share_icon_transparent.png")
                )
            ),
            strings._("gui_website_mode_no_files"),
            strings._("gui_all_modes_history"),
            "download",
        )
        self.history.requests_label.hide()
        self.history.hide()

        # Info label
        self.info_label = QtWidgets.QLabel()
        self.info_label.hide()

        # Toggle history
        self.toggle_history = ToggleHistory(
            self.common,
            self,
            self.history,
            QtGui.QIcon(
                GuiCommon.get_resource_path(
                    f"images/{self.common.gui.color_mode}_history_icon_toggle.svg"
                )
            ),
            QtGui.QIcon(
                GuiCommon.get_resource_path(
                    f"images/{self.common.gui.color_mode}_history_icon_toggle_selected.svg"
                )
            ),
        )

        # Top bar
        top_bar_layout = QtWidgets.QHBoxLayout()
        # Add space at the top, same height as the toggle history bar in other modes
        top_bar_layout.addWidget(MinimumSizeWidget(0, 30))
        top_bar_layout.addWidget(self.info_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.toggle_history)

        # Primary action layout
        self.primary_action.hide()
        self.update_primary_action()

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addWidget(header_label)
        self.main_layout.addWidget(self.download_mode_explainer)
        self.main_layout.addWidget(self.primary_action, stretch=1)
        self.main_layout.addWidget(self.server_status)
        self.main_layout.addWidget(MinimumSizeWidget(700, 0))

        # Column layout
        self.column_layout = QtWidgets.QHBoxLayout()
        self.column_layout.addWidget(self.image)
        self.column_layout.addLayout(self.main_layout)
        self.column_layout.addWidget(self.history, stretch=1)

        # Content layout
        self.content_layout.addLayout(self.column_layout)

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "download"

    def onionshare_uses_private_key_checkbox_checked(self):
        """
        If the user checked the box saying a Private Key was sent, show the private key lineEdit field.
        """
        if self.onionshare_uses_private_key_checkbox.isChecked():
            self.onionshare_private_key.show()
        else:
            self.onionshare_private_key.hide()

    def data_dir_button_clicked(self):
        """
        Browse for a new OnionShare data directory, and save to tab settings
        """
        data_dir = self.data_dir_lineedit.text()
        selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, strings._("mode_settings_receive_data_dir_label"), data_dir
        )

        if selected_dir:
            # If we're running inside a flatpak package, the data dir must be inside ~/OnionShare
            if self.common.gui.is_flatpak:
                if not selected_dir.startswith(os.path.expanduser("~/OnionShare")):
                    Alert(self.common, strings._("gui_receive_flatpak_data_dir"))
                    return

            self.common.log(
                "DownloadMode",
                "data_dir_button_clicked",
                f"selected dir: {selected_dir}",
            )
            self.data_dir_lineedit.setText(selected_dir)
            self.settings.set("download", "data_dir", selected_dir)

    def poll_checkbox_checked(self):
        """
        If the user checks the poll option or changes the value of the poll interval
        when it is checkced, set the poll interval in settings.
        """
        if self.poll_checkbox.isChecked():
            self.common.log(
                "DownloadMode",
                "poll_checkbox_checked",
                f"Set poll to : {self.poll.value()}",
            )
            self.settings.set("download", "poll", self.poll.value())
            self.poll_warning_label.show()
        else:
            self.settings.set("download", "poll", 0)
            self.poll_warning_label.hide()

    def extract_domain(self, url):
        # First, parse the URL to get the domain
        parsed_url = urlparse(url)

        # Extract the domain (without scheme and path)
        domain_with_tld = parsed_url.netloc.split(":")[0]  # Remove port if any

        # Regular expression to extract the main domain name
        match = re.search(r"([a-zA-Z0-9-]+)\.[a-zA-Z]{2,}", domain_with_tld)

        if match:
            return match.group(1)
        else:
            return None  # Return None if no domain is found

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        self.common.log("Mode", "start_server")
        self.id += 1

        self.set_server_active.emit(True)

        # Hide and reset the downloads if we have previously shared
        self.reset_info_counters()

        # Clear the status bar
        self.status_bar.clearMessage()
        self.server_status_label.setText("")

        # Hide the mode settings
        self.mode_settings_widget.hide()

        self.service_id = self.extract_domain(self.onionshare_url.text().strip())

        self.common.log("DownloadMode", "start_server")

        if not self.common.gui.local_only:
            self.download_thread = DownloadThread(self)

            self.download_thread.begun.connect(self.add_download_item)
            self.download_thread.progress.connect(self.progress_download_item)
            self.download_thread.success.connect(self.finished_download_item)
            self.download_thread.error.connect(self.error_download_item)
            self.download_thread.locked.connect(self.locked_download_item)

            # Start the download thread
            self.download_thread.start()

            if (
                self.settings.get("download", "poll")
                and self.settings.get("download", "poll") >= 1
            ):
                self.is_polling = True
                # Set up a QTimer to trigger the thread at end of each polling interval
                self.timer = QtCore.QTimer(self)
                self.timer.timeout.connect(self.trigger_download_thread)
                self.timer.setInterval(
                    self.settings.get("download", "poll") * 60 * 1000
                )  # Minutes to milliseconds
                self.timer.start()

        # Update the 'Explainer' label to explain what is happening.
        if self.is_polling:
            self.download_mode_explainer.setText(
                strings._("gui_download_mode_in_progress_polling").format(
                    self.onionshare_url.text().strip(), self.poll.value()
                )
            )
        else:
            self.download_mode_explainer.setText(
                strings._("gui_download_mode_in_progress").format(
                    self.onionshare_url.text().strip()
                )
            )

    def trigger_download_thread(self):
        if not self.download_thread._lock:
            self.download_thread.start()

    def start_server_step2_custom(self):
        # Continue
        self.starting_server_step3.emit()
        self.start_server_finished.emit()

    def cancel_server_custom(self):
        """
        Log that the server has been cancelled
        """
        self.common.log("DownloadMode", "cancel_server")

    def stop_server_custom(self):
        """
        If any polling is taking place, stop iot
        """
        if self.is_polling:
            self.common.log(
                "DownloadMode", "stop_server_custom", "Stopping Download polling timer"
            )
            self.timer.stop()
        if self.download_thread:
            self.common.log(
                "DownloadMode", "stop_server_custom", "Stopping DownloadThread"
            )
            self.download_thread.quit()
            self.download_thread.wait()

        self.common.gui.onion.remove_onion_client_auth(self.service_id)
        self.download_mode_explainer.setText(strings._("gui_download_mode_explainer"))

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()

    def update_primary_action(self):
        self.common.log("DownloadMode", "update_primary_action")

        # Show or hide primary action layout
        self.primary_action.show()
        self.info_label.show()

    def add_download_item(self):
        self.common.log("DownloadMode", "add_download_item", self.id)
        item = DownloadHistoryItem(
            self.common,
            self.id,
            self.onionshare_url.text().strip(),
        )

        self.history.add(self.id, item)
        self.toggle_history.update_indicator(True)
        self.history.in_progress_count += 1
        self.history.update_in_progress()

    def progress_download_item(self, progress):
        self.common.log(
            "DownloadMode", "progress_download_item", f"Progress: {progress}%"
        )
        self.history.update(self.id, {"action": "progress", "progress": progress})
        self.history.update_in_progress()

    def finished_download_item(self, file_path, file_name, file_size):
        self.common.log(
            "DownloadMode",
            "finished_download_item",
            f"File path is {file_path}, file name is {file_name}, file size is {file_size}",
        )
        self.history.update(
            self.id,
            {
                "action": "finished",
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
            },
        )
        self.history.completed_count += 1
        self.history.in_progress_count -= 1
        self.history.update_completed()
        self.history.update_in_progress()

        self.start_server_step2_custom()
        if not self.is_polling:
            self.stop_server()

    def locked_download_item(self):
        self.common.log(
            "DownloadMode",
            "locked_download_item",
            "Thread is locked, a download must be running",
        )
        if self.history.in_progress_count > 0:
            self.history.in_progress_count -= 1

    def error_download_item(self, error):
        self.common.log("DownloadMode", "error_download_item", f"{self.id}: {error}")
        self.history.update(self.id, {"action": "error", "error": error})
        if self.history.in_progress_count > 0:
            self.history.in_progress_count -= 1
            self.history.update_in_progress()
        if not self.is_polling:
            self.stop_server()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.history.reset()
        self.toggle_history.indicator_count = 0
        self.toggle_history.update_indicator()
