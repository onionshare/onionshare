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

from PySide6 import QtCore, QtWidgets, QtGui

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
    Parts of the main window UI for sharing websites.
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def init(self):
        """
        Custom initialization for WebsiteMode.
        """
        # Create the Web object
        self.web = Web(self.common, True, self.settings, "website")

        # Back Button
        self.back_button = QtWidgets.QPushButton(strings._("gui_back_button"))
        self.back_button.clicked.connect(self.go_back)  # Connect to back logic
        self.back_button.setStyleSheet(self.common.gui.css["mode_button"])

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
        top_bar_layout.addWidget(self.back_button)  # Add Back button to the top bar
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

    def go_back(self):
        """
        Handle navigation to the main menu.
        """
        self.common.gui.switch_to_tab("main_menu")  # Navigate back to the main menu

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "website"

    # Additional methods remain unchanged
