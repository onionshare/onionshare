# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.web import Web

from ..history import History, ToggleHistory, ReceiveHistoryItem
from .. import Mode
from .... import strings
from ....widgets import MinimumWidthWidget, Alert
from ....gui_common import GuiCommon


class ReceiveMode(Mode):
    """
    Parts of the main window UI for receiving files.
    """

    def init(self):
        """
        Custom initialization for ReceiveMode.
        """
        # Create the Web object
        self.web = Web(self.common, True, self.settings, "receive")

        # Receive image
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
        self.image_label.setFixedSize(250, 250)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.image_label)
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # Settings
        data_dir_label = QtWidgets.QLabel(
            strings._("mode_settings_receive_data_dir_label")
        )
        self.data_dir_lineedit = QtWidgets.QLineEdit()
        self.data_dir_lineedit.setReadOnly(True)
        self.data_dir_lineedit.setText(self.settings.get("receive", "data_dir"))
        data_dir_button = QtWidgets.QPushButton(
            strings._("mode_settings_receive_data_dir_browse_button")
        )
        data_dir_button.clicked.connect(self.data_dir_button_clicked)
        data_dir_layout = QtWidgets.QHBoxLayout()
        data_dir_layout.addWidget(data_dir_label)
        data_dir_layout.addWidget(self.data_dir_lineedit)
        data_dir_layout.addWidget(data_dir_button)

        self.mode_settings_widget.mode_specific_layout.addLayout(data_dir_layout)

        # Server status
        self.server_status.set_mode("receive")
        self.server_status.server_started_finished.connect(self.update_primary_action)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.update_primary_action)

        # Tell server_status about web, then update
        self.server_status.web = self.web
        self.server_status.update()

        # Upload history
        self.history = History(
            self.common,
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path("images/receive_icon_transparent.png")
                )
            ),
            strings._("gui_receive_mode_no_files"),
            strings._("gui_all_modes_history"),
        )
        self.history.hide()

        # Toggle history
        self.toggle_history = ToggleHistory(
            self.common,
            self,
            self.history,
            QtGui.QIcon(GuiCommon.get_resource_path("images/receive_icon_toggle.png")),
            QtGui.QIcon(
                GuiCommon.get_resource_path("images/receive_icon_toggle_selected.png")
            ),
        )

        # Header
        header_label = QtWidgets.QLabel(strings._("gui_new_tab_receive_button"))
        header_label.setStyleSheet(self.common.gui.css["mode_header_label"])

        # Receive mode warning
        receive_warning = QtWidgets.QLabel(strings._("gui_receive_mode_warning"))
        receive_warning.setMinimumHeight(80)
        receive_warning.setWordWrap(True)

        # Top bar
        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.toggle_history)

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(header_label)
        self.main_layout.addWidget(receive_warning)
        self.main_layout.addWidget(self.primary_action)
        self.main_layout.addWidget(MinimumWidthWidget(525))

        # Row layout
        content_row = QtWidgets.QHBoxLayout()
        content_row.addLayout(self.main_layout)
        content_row.addWidget(self.image)
        row_layout = QtWidgets.QVBoxLayout()
        row_layout.addLayout(top_bar_layout)
        row_layout.addStretch()
        row_layout.addLayout(content_row)
        row_layout.addWidget(self.server_status)
        row_layout.addStretch()

        # Column layout
        self.column_layout = QtWidgets.QHBoxLayout()
        self.column_layout.addLayout(row_layout)
        self.column_layout.addWidget(self.history, stretch=1)

        # Wrapper layout
        self.wrapper_layout = QtWidgets.QVBoxLayout()
        self.wrapper_layout.addLayout(self.column_layout)
        self.setLayout(self.wrapper_layout)

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "receive"

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
                "ReceiveMode",
                "data_dir_button_clicked",
                f"selected dir: {selected_dir}",
            )
            self.data_dir_lineedit.setText(selected_dir)
            self.settings.set("receive", "data_dir", selected_dir)

    def get_stop_server_autostop_timer_text(self):
        """
        Return the string to put on the stop server button, if there's an auto-stop timer
        """
        return strings._("gui_receive_stop_server_autostop_timer")

    def autostop_timer_finished_should_stop_server(self):
        """
        The auto-stop timer expired, should we stop the server? Returns a bool
        """
        # If there were no attempts to upload files, or all uploads are done, we can stop
        if (
            self.web.receive_mode.cur_history_id == 0
            or not self.web.receive_mode.uploads_in_progress
        ):
            self.server_status.stop_server()
            self.server_status_label.setText(strings._("close_on_autostop_timer"))
            return True
        # An upload is probably still running - hold off on stopping the share, but block new shares.
        else:
            self.server_status_label.setText(
                strings._("gui_receive_mode_autostop_timer_waiting")
            )
            self.web.receive_mode.can_upload = False
            return False

    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.receive_mode.cur_history_id = 0
        self.web.reset_invalid_passwords()

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

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        self.system_tray.showMessage(
            strings._("systray_page_loaded_title"),
            strings._("systray_page_loaded_message"),
        )

    def handle_request_started(self, event):
        """
        Handle REQUEST_STARTED event.
        """
        item = ReceiveHistoryItem(
            self.common, event["data"]["id"], event["data"]["content_length"]
        )
        self.history.add(event["data"]["id"], item)
        self.toggle_history.update_indicator(True)
        self.history.in_progress_count += 1
        self.history.update_in_progress()

        self.system_tray.showMessage(
            strings._("systray_receive_started_title"),
            strings._("systray_receive_started_message"),
        )

    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        self.history.update(
            event["data"]["id"],
            {"action": "progress", "progress": event["data"]["progress"]},
        )

    def handle_request_upload_file_renamed(self, event):
        """
        Handle REQUEST_UPLOAD_FILE_RENAMED event.
        """
        self.history.update(
            event["data"]["id"],
            {
                "action": "rename",
                "old_filename": event["data"]["old_filename"],
                "new_filename": event["data"]["new_filename"],
            },
        )

    def handle_request_upload_set_dir(self, event):
        """
        Handle REQUEST_UPLOAD_SET_DIR event.
        """
        self.history.update(
            event["data"]["id"],
            {
                "action": "set_dir",
                "filename": event["data"]["filename"],
                "dir": event["data"]["dir"],
            },
        )

    def handle_request_upload_finished(self, event):
        """
        Handle REQUEST_UPLOAD_FINISHED event.
        """
        self.history.update(event["data"]["id"], {"action": "finished"})
        self.history.completed_count += 1
        self.history.in_progress_count -= 1
        self.history.update_completed()
        self.history.update_in_progress()

    def handle_request_upload_canceled(self, event):
        """
        Handle REQUEST_UPLOAD_CANCELED event.
        """
        self.history.update(event["data"]["id"], {"action": "canceled"})
        self.history.in_progress_count -= 1
        self.history.update_in_progress()

    def on_reload_settings(self):
        """
        We should be ok to re-enable the 'Start Receive Mode' button now.
        """
        self.primary_action.show()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.history.reset()
        self.toggle_history.indicator_count = 0
        self.toggle_history.update_indicator()

    def update_primary_action(self):
        self.common.log("ReceiveMode", "update_primary_action")
