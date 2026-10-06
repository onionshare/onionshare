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
import tempfile

from PySide6 import QtCore, QtWidgets, QtGui

from onionshare_cli.web import Web

from ..history import History, ToggleHistory, ReceiveHistoryItem
from .. import Mode
from .... import strings
from ....widgets import MinimumSizeWidget, Alert
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

        # Data dir
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

        # Disable text or files
        self.disable_text_checkbox = self.settings.get("receive", "disable_files")
        self.disable_text_checkbox = QtWidgets.QCheckBox()
        self.disable_text_checkbox.clicked.connect(self.disable_text_checkbox_clicked)
        self.disable_text_checkbox.setText(
            strings._("mode_settings_receive_disable_text_checkbox")
        )
        self.disable_text_checkbox.setStyleSheet(self.common.gui.css["receive_options"])
        self.disable_files_checkbox = self.settings.get("receive", "disable_files")
        self.disable_files_checkbox = QtWidgets.QCheckBox()
        self.disable_files_checkbox.clicked.connect(self.disable_files_checkbox_clicked)
        self.disable_files_checkbox.setText(
            strings._("mode_settings_receive_disable_files_checkbox")
        )
        self.disable_files_checkbox.setStyleSheet(self.common.gui.css["receive_options"])
        disable_layout = QtWidgets.QHBoxLayout()
        disable_layout.addWidget(self.disable_text_checkbox)
        disable_layout.addWidget(self.disable_files_checkbox)
        disable_layout.addStretch()
        self.mode_settings_widget.mode_specific_layout.addLayout(disable_layout)

        # Maximum upload size
        self.max_upload_size_checkbox = QtWidgets.QCheckBox()
        self.max_upload_size_checkbox.clicked.connect(
            self.max_upload_size_checkbox_clicked
        )
        self.max_upload_size_checkbox.setText(
            strings._("mode_settings_receive_max_upload_size_checkbox")
        )
        self.max_upload_size_spinbox = QtWidgets.QDoubleSpinBox()
        self.max_upload_size_spinbox.setMinimum(0.1)
        self.max_upload_size_spinbox.setMaximum(1000000.0)
        self.max_upload_size_spinbox.setDecimals(1)
        self.max_upload_size_unit_combobox = QtWidgets.QComboBox()
        self.max_upload_size_unit_combobox.addItem(
            strings._("mode_settings_receive_max_upload_size_unit_kb"), 1024
        )
        self.max_upload_size_unit_combobox.addItem(
            strings._("mode_settings_receive_max_upload_size_unit_mb"), 1024**2
        )
        self.max_upload_size_unit_combobox.addItem(
            strings._("mode_settings_receive_max_upload_size_unit_gb"), 1024**3
        )
        max_upload_size_layout = QtWidgets.QHBoxLayout()
        max_upload_size_layout.addWidget(self.max_upload_size_checkbox)
        max_upload_size_layout.addWidget(self.max_upload_size_spinbox)
        max_upload_size_layout.addWidget(self.max_upload_size_unit_combobox)
        max_upload_size_layout.addStretch()
        self.mode_settings_widget.mode_specific_layout.addLayout(max_upload_size_layout)

        # Apply the maximum upload size to the service's entire lifespan
        self.max_upload_size_total_checkbox = QtWidgets.QCheckBox()
        self.max_upload_size_total_checkbox.clicked.connect(
            self.max_upload_size_total_checkbox_clicked
        )
        self.max_upload_size_total_checkbox.setText(
            strings._("mode_settings_receive_max_upload_size_total_checkbox")
        )
        self.mode_settings_widget.mode_specific_layout.addWidget(
            self.max_upload_size_total_checkbox
        )

        # Load the saved maximum upload size, if any
        max_upload_size = self.settings.get("receive", "max_upload_size")
        if max_upload_size > 0:
            self.max_upload_size_checkbox.setCheckState(QtCore.Qt.Checked)
            self.max_upload_size_total_checkbox.setEnabled(True)
            if self.settings.get("receive", "max_upload_size_total"):
                self.max_upload_size_total_checkbox.setCheckState(QtCore.Qt.Checked)
            else:
                self.max_upload_size_total_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.set_max_upload_size_widgets(max_upload_size)
            self.show_max_upload_size()
        else:
            self.max_upload_size_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.max_upload_size_total_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.max_upload_size_total_checkbox.setEnabled(False)
            self.set_max_upload_size_widgets(5 * 1024**2)
            self.hide_max_upload_size()

        # Connect these after loading their initial values, so setting them
        # doesn't trigger a save
        self.max_upload_size_spinbox.valueChanged.connect(self.max_upload_size_edited)
        self.max_upload_size_unit_combobox.currentIndexChanged.connect(
            self.max_upload_size_edited
        )

        # Webhook URL
        webhook_url = self.settings.get("receive", "webhook_url")
        self.webhook_url_checkbox = QtWidgets.QCheckBox()
        self.webhook_url_checkbox.clicked.connect(self.webhook_url_checkbox_clicked)
        self.webhook_url_checkbox.setText(
            strings._("mode_settings_receive_webhook_url_checkbox")
        )
        self.webhook_url_lineedit = QtWidgets.QLineEdit()
        self.webhook_url_lineedit.editingFinished.connect(
            self.webhook_url_editing_finished
        )
        self.webhook_url_lineedit.setPlaceholderText(
            "https://example.com/post-when-file-uploaded"
        )
        webhook_url_layout = QtWidgets.QHBoxLayout()
        webhook_url_layout.addWidget(self.webhook_url_checkbox)
        webhook_url_layout.addWidget(self.webhook_url_lineedit)
        if webhook_url is not None and webhook_url != "":
            self.webhook_url_checkbox.setCheckState(QtCore.Qt.Checked)
            self.webhook_url_lineedit.setText(
                self.settings.get("receive", "webhook_url")
            )
            self.show_webhook_url()
        else:
            self.webhook_url_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.hide_webhook_url()
        self.mode_settings_widget.mode_specific_layout.addLayout(webhook_url_layout)

        # Set title placeholder
        self.mode_settings_widget.title_lineedit.setPlaceholderText(
            strings._("gui_tab_name_receive")
        )

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
            QtGui.QIcon(GuiCommon.get_resource_path(f"images/{self.common.gui.color_mode}_history_icon_toggle.svg")),
            QtGui.QIcon(
                GuiCommon.get_resource_path(f"images/{self.common.gui.color_mode}_history_icon_toggle_selected.svg")
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
        self.main_layout.addWidget(self.primary_action, stretch=1)
        self.main_layout.addWidget(self.server_status)

        # Row layout
        content_row = QtWidgets.QHBoxLayout()
        content_row.addLayout(self.main_layout, stretch=1)
        content_row.addWidget(self.image)
        row_layout = QtWidgets.QVBoxLayout()
        row_layout.addLayout(top_bar_layout)
        row_layout.addLayout(content_row, stretch=1)

        # Column layout
        self.column_layout = QtWidgets.QHBoxLayout()
        self.column_layout.addLayout(row_layout)
        self.column_layout.addWidget(self.history, stretch=1)

        # Content layout
        self.content_layout.addLayout(self.column_layout)

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "receive"

    @staticmethod
    def is_data_dir_writable(path, create=False):
        """
        Return True if path is a directory we can create files in.

        At server startup, create missing directories as uploads historically did.
        Directory selection checks remain read-only apart from the write probe.

        Uses a real write probe so AppArmor/sandbox restrictions (e.g. Tails)
        are detected even when os.access is optimistic.
        """
        if not path:
            return False
        try:
            if create:
                os.makedirs(path, mode=0o700, exist_ok=True)
            if not os.path.isdir(path):
                return False
            with tempfile.TemporaryDirectory(
                prefix=".onionshare-write-test-",
                dir=path,
            ) as probe_dir:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix="probe-",
                    dir=probe_dir,
                ) as probe:
                    probe.write(b"ok")
                    probe.flush()

            return True
        except OSError:
            return False

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

            if not self.is_data_dir_writable(selected_dir):
                Alert(
                    self.common,
                    strings._("gui_receive_data_dir_not_writable").format(selected_dir),
                    QtWidgets.QMessageBox.Warning,
                )
                return

            self.common.log(
                "ReceiveMode",
                "data_dir_button_clicked",
                f"selected dir: {selected_dir}",
            )
            self.data_dir_lineedit.setText(selected_dir)
            self.settings.set("receive", "data_dir", selected_dir)

    def disable_text_checkbox_clicked(self):
        self.settings.set(
            "receive", "disable_text", self.disable_text_checkbox.isChecked()
        )
        if self.disable_text_checkbox.isChecked():
            # Prevent also disabling files if text is disabled
            self.disable_files_checkbox.setDisabled(True)
        else:
            self.disable_files_checkbox.setDisabled(False)

    def disable_files_checkbox_clicked(self):
        self.settings.set(
            "receive", "disable_files", self.disable_files_checkbox.isChecked()
        )
        if self.disable_files_checkbox.isChecked():
            # Prevent also disabling text if files is disabled
            self.disable_text_checkbox.setDisabled(True)
        else:
            self.disable_text_checkbox.setDisabled(False)

    def webhook_url_checkbox_clicked(self):
        if self.webhook_url_checkbox.isChecked():
            if self.settings.get("receive", "webhook_url"):
                self.webhook_url_lineedit.setText(
                    self.settings.get("receive", "webhook_url")
                )
            self.show_webhook_url()
        else:
            self.settings.set("receive", "webhook_url", None)
            self.hide_webhook_url()

    def webhook_url_editing_finished(self):
        self.settings.set("receive", "webhook_url", self.webhook_url_lineedit.text())

    def hide_webhook_url(self):
        self.webhook_url_lineedit.hide()

    def show_webhook_url(self):
        self.webhook_url_lineedit.show()

    def max_upload_size_checkbox_clicked(self):
        if self.max_upload_size_checkbox.isChecked():
            self.show_max_upload_size()
            self.max_upload_size_total_checkbox.setEnabled(True)
            self.save_max_upload_size()
        else:
            self.hide_max_upload_size()
            self.max_upload_size_total_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.max_upload_size_total_checkbox.setEnabled(False)
            self.settings.set("receive", "max_upload_size", 0)
            self.settings.set("receive", "max_upload_size_total", False)

    def max_upload_size_edited(self):
        if self.max_upload_size_checkbox.isChecked():
            self.save_max_upload_size()

    def max_upload_size_total_checkbox_clicked(self):
        self.settings.set(
            "receive",
            "max_upload_size_total",
            self.max_upload_size_total_checkbox.isChecked(),
        )

    def save_max_upload_size(self):
        value = self.max_upload_size_spinbox.value()
        unit = self.max_upload_size_unit_combobox.currentData()
        self.settings.set("receive", "max_upload_size", int(value * unit))

    def set_max_upload_size_widgets(self, size):
        """
        Load a size in bytes into the value/unit widgets, using the largest
        unit that keeps the value >= 1.
        """
        units = [(1024**3, 2), (1024**2, 1), (1024, 0)]
        for multiplier, index in units:
            if size >= multiplier:
                self.max_upload_size_unit_combobox.setCurrentIndex(index)
                self.max_upload_size_spinbox.setValue(size / multiplier)
                return
        # Smaller than 1 KiB: show it in KB anyway
        self.max_upload_size_unit_combobox.setCurrentIndex(0)
        self.max_upload_size_spinbox.setValue(max(size / 1024, 0.1))

    def show_max_upload_size(self):
        self.max_upload_size_spinbox.show()
        self.max_upload_size_unit_combobox.show()
        self.max_upload_size_total_checkbox.show()

    def hide_max_upload_size(self):
        self.max_upload_size_spinbox.hide()
        self.max_upload_size_unit_combobox.hide()
        self.max_upload_size_total_checkbox.hide()

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

    def start_server(self):
        """
        Start Receive Mode only if the save directory is writable.
        """
        data_dir = self.settings.get("receive", "data_dir")
        if not self.is_data_dir_writable(data_dir, create=True):
            self.server_status.stop_server_finished()
            Alert(
                self.common,
                strings._("gui_receive_data_dir_not_writable").format(data_dir),
                QtWidgets.QMessageBox.Warning,
            )
            return
        super().start_server()

    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.receive_mode.cur_history_id = 0

        # Hide and reset the uploads if we have previously shared
        self.reset_info_counters()

        # Set proxies for webhook URL
        if self.common.gui.local_only:
            self.web.proxies = None
        else:
            (socks_address, socks_port) = self.common.gui.onion.get_tor_socks_port()
            self.web.proxies = {
                "http": f"socks5h://{socks_address}:{socks_port}",
                "https": f"socks5h://{socks_address}:{socks_port}",
            }

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
            self.common,
            event["data"]["id"],
            event["data"]["content_length"],
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

    def handle_request_upload_includes_message(self, event):
        """
        Handle REQUEST_UPLOAD_INCLUDES_MESSAGE event.
        """
        self.history.includes_message(event["data"]["id"], event["data"]["filename"])

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

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.history.reset()
        self.toggle_history.indicator_count = 0
        self.toggle_history.update_indicator()

    def update_primary_action(self):
        self.common.log("ReceiveMode", "update_primary_action")
