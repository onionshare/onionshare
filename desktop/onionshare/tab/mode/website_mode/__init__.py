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

from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.common import Common
from onionshare_cli.web import Web

from .. import Mode
from ..file_selection import FileSelection
from ..history import History, ToggleHistory
from .... import strings
from ....widgets import MinimumSizeWidget
from ....gui_common import GuiCommon


class WebsiteMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def init(self):
        """
        Custom initialization for ReceiveMode.
        """
        # Create the Web object
        self.web = Web(self.common, True, self.settings, "website")

        # Settings
        # Disable CSP option
        self.disable_csp_checkbox = QtWidgets.QCheckBox()
        self.disable_csp_checkbox.clicked.connect(self.disable_csp_checkbox_clicked)
        self.disable_csp_checkbox.setText(
            strings._("mode_settings_website_disable_csp_checkbox")
        )
        if self.settings.get("website", "disable_csp"):
            self.disable_csp_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.disable_csp_checkbox.setCheckState(QtCore.Qt.Unchecked)

        self.mode_settings_widget.mode_specific_layout.addWidget(
            self.disable_csp_checkbox
        )

        # Custom CSP option
        self.custom_csp_checkbox = QtWidgets.QCheckBox()
        self.custom_csp_checkbox.clicked.connect(self.custom_csp_checkbox_clicked)
        self.custom_csp_checkbox.setText(strings._("mode_settings_website_custom_csp_checkbox"))
        if self.settings.get("website", "custom_csp") and not self.settings.get("website", "disable_csp"):
            self.custom_csp_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.custom_csp_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.custom_csp = QtWidgets.QLineEdit()
        self.custom_csp.setPlaceholderText(
            "default-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'; img-src 'self' data:;"
        )
        self.custom_csp.editingFinished.connect(self.custom_csp_editing_finished)

        custom_csp_layout = QtWidgets.QHBoxLayout()
        custom_csp_layout.setContentsMargins(0, 0, 0, 0)
        custom_csp_layout.addWidget(self.custom_csp_checkbox)
        custom_csp_layout.addWidget(self.custom_csp)
        self.mode_settings_widget.mode_specific_layout.addLayout(custom_csp_layout)

        # File selection
        self.file_selection = FileSelection(
            self.common,
            "images/{}_mode_website.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_website_button"),
            self,
        )
        if self.filenames:
            for filename in self.filenames:
                self.file_selection.file_list.add_file(filename)

        # Set title placeholder
        self.mode_settings_widget.title_lineedit.setPlaceholderText(
            strings._("gui_tab_name_website")
        )

        # Server status
        self.server_status.set_mode("website", self.file_selection)
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
        self.filesize_warning.setStyleSheet(
            self.common.gui.css["share_filesize_warning"]
        )
        self.filesize_warning.hide()

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
            "website",
        )
        self.history.in_progress_label.hide()
        self.history.completed_label.hide()
        self.history.hide()

        # Info label
        self.info_label = QtWidgets.QLabel()
        self.info_label.hide()

        # Delete all files button
        self.remove_all_button = QtWidgets.QPushButton(
            strings._("gui_file_selection_remove_all")
        )
        self.remove_all_button.setFlat(True)
        self.remove_all_button.setStyleSheet(
            self.common.gui.css["share_delete_all_files_button"]
        )
        self.remove_all_button.clicked.connect(self.delete_all)
        self.remove_all_button.hide()

        # Toggle history
        self.toggle_history = ToggleHistory(
            self.common,
            self,
            self.history,
            QtGui.QIcon(GuiCommon.get_resource_path("images/share_icon_toggle.png")),
            QtGui.QIcon(
                GuiCommon.get_resource_path("images/share_icon_toggle_selected.png")
            ),
        )

        # Top bar
        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.addWidget(self.info_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.remove_all_button)
        top_bar_layout.addWidget(self.toggle_history)

        # Primary action layout
        self.primary_action_layout.addWidget(self.filesize_warning)
        self.primary_action.hide()
        self.update_primary_action()

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addLayout(self.file_selection)
        self.main_layout.addWidget(self.primary_action, stretch=1)
        self.main_layout.addWidget(self.server_status)
        self.main_layout.addWidget(MinimumSizeWidget(700, 0))

        # Column layout
        self.column_layout = QtWidgets.QHBoxLayout()
        self.column_layout.addLayout(self.main_layout)
        self.column_layout.addWidget(self.history, stretch=1)

        # Content layout
        self.content_layout.addLayout(self.column_layout)

        # Always start with focus on file selection
        self.file_selection.setFocus()

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "website"

    def disable_csp_checkbox_clicked(self):
        """
        Save disable CSP setting to the tab settings. Uncheck 'custom CSP'
        setting if disabling CSP altogether.
        """
        self.settings.set(
            "website", "disable_csp", self.disable_csp_checkbox.isChecked()
        )
        if self.disable_csp_checkbox.isChecked():
            self.custom_csp_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.custom_csp_checkbox.setEnabled(False)
        else:
            self.custom_csp_checkbox.setEnabled(True)

    def custom_csp_checkbox_clicked(self):
        """
        Uncheck 'disable CSP' setting if custom CSP is used.
        """
        if self.custom_csp_checkbox.isChecked():
            self.disable_csp_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.disable_csp_checkbox.setEnabled(False)
            self.settings.set(
                "website", "custom_csp", self.custom_csp
            )
        else:
            self.disable_csp_checkbox.setEnabled(True)
            self.custom_csp.setText("")
            self.settings.set(
                "website", "custom_csp", None
            )

    def custom_csp_editing_finished(self):
        if self.custom_csp.text().strip() == "":
            self.custom_csp.setText("")
            self.settings.set("website", "custom_csp", None)
        else:
            custom_csp = self.custom_csp.text()
            self.settings.set("website", "custom_csp", custom_csp)

    def get_stop_server_autostop_timer_text(self):
        """
        Return the string to put on the stop server button, if there's an auto-stop timer
        """
        return strings._("gui_share_stop_server_autostop_timer")

    def autostop_timer_finished_should_stop_server(self):
        """
        The auto-stop timer expired, should we stop the server? Returns a bool
        """

        self.server_status.stop_server()
        self.server_status_label.setText(strings._("close_on_autostop_timer"))
        return True

    def start_server_custom(self):
        """
        Starting the server.
        """
        # Reset web counters
        self.web.website_mode.visit_count = 0

        # Hide and reset the downloads if we have previously shared
        self.reset_info_counters()

        self.remove_all_button.hide()

    def start_server_step2_custom(self):
        """
        Step 2 in starting the server. Zipping up files.
        """
        self.filenames = []
        for index in range(self.file_selection.file_list.count()):
            self.filenames.append(self.file_selection.file_list.item(index).filename)

        # Continue
        self.starting_server_step3.emit()
        self.start_server_finished.emit()

    def start_server_step3_custom(self):
        """
        Step 3 in starting the server. Display large filesize
        warning, if applicable.
        """
        self.web.website_mode.set_file_info(self.filenames)
        self.success.emit()

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

        self.filesize_warning.hide()
        self.history.completed_count = 0
        self.file_selection.file_list.adjustSize()

        self.remove_all_button.show()

    def cancel_server_custom(self):
        """
        Log that the server has been cancelled
        """
        self.common.log("WebsiteMode", "cancel_server")

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()

    def on_reload_settings(self):
        """
        If there were some files listed for sharing, we should be ok to re-enable
        the 'Start Sharing' button now.
        """
        if self.server_status.file_selection.get_num_files() > 0:
            self.primary_action.show()
            self.info_label.show()
            self.remove_all_button.show()

    def update_primary_action(self):
        self.common.log("WebsiteMode", "update_primary_action")

        # Show or hide primary action layout
        file_count = self.file_selection.file_list.count()
        if file_count > 0:
            self.primary_action.show()
            self.info_label.show()
            self.remove_all_button.show()

            # Update the file count in the info label
            total_size_bytes = 0
            for index in range(self.file_selection.file_list.count()):
                item = self.file_selection.file_list.item(index)
                total_size_bytes += item.size_bytes
            total_size_readable = self.common.human_readable_filesize(total_size_bytes)

            if file_count > 1:
                self.info_label.setText(
                    strings._("gui_file_info").format(file_count, total_size_readable)
                )
            else:
                self.info_label.setText(
                    strings._("gui_file_info_single").format(
                        file_count, total_size_readable
                    )
                )

        else:
            self.primary_action.hide()
            self.info_label.hide()
            self.remove_all_button.hide()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.history.reset()
        self.toggle_history.indicator_count = 0
        self.toggle_history.update_indicator()

    def delete_all(self):
        """
        Delete All button clicked
        """
        self.file_selection.file_list.clear()
        self.file_selection.file_list.files_updated.emit()

        self.file_selection.file_list.setCurrentItem(None)

    @staticmethod
    def _compute_total_size(filenames):
        total_size = 0
        for filename in filenames:
            if os.path.isfile(filename):
                total_size += os.path.getsize(filename)
            if os.path.isdir(filename):
                total_size += Common.dir_size(filename)
        return total_size
