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

from .threads import CompressThread
from .. import Mode
from ..file_selection import FileSelection
from ..history import History, ToggleHistory, ShareHistoryItem
from .... import strings
from ....widgets import MinimumSizeWidget
from ....gui_common import GuiCommon


class ShareMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """

    def init(self):
        """
        Custom initialization for ShareMode.
        """
        # Threads start out as None
        self.compress_thread = None

        # Create the Web object
        self.web = Web(self.common, True, self.settings, "share")

        # Back Button
        self.back_button = QtWidgets.QPushButton(strings._("gui_back_button"))
        self.back_button.clicked.connect(self.go_back)  # Connect to back logic
        self.back_button.setStyleSheet(self.common.gui.css["mode_button"])

        # Settings
        self.autostop_sharing_checkbox = QtWidgets.QCheckBox()
        self.autostop_sharing_checkbox.clicked.connect(
            self.autostop_sharing_checkbox_clicked
        )
        self.autostop_sharing_checkbox.setText(
            strings._("mode_settings_share_autostop_sharing_checkbox")
        )
        if self.settings.get("share", "autostop_sharing"):
            self.autostop_sharing_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autostop_sharing_checkbox.setCheckState(QtCore.Qt.Unchecked)

        self.mode_settings_widget.mode_specific_layout.addWidget(
            self.autostop_sharing_checkbox
        )

        # File selection
        self.file_selection = FileSelection(
            self.common,
            "images/{}_mode_share.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_share_button"),
            self,
        )
        if self.filenames:
            for filename in self.filenames:
                self.file_selection.file_list.add_file(filename)

        # Set title placeholder
        self.mode_settings_widget.title_lineedit.setPlaceholderText(
            strings._("gui_tab_name_share")
        )

        # Server status
        self.server_status.set_mode("share", self.file_selection)
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
            strings._("gui_share_mode_no_files"),
            strings._("gui_all_modes_history"),
        )
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

        # Status bar, zip progress bar
        self._zip_progress_bar = None

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
        return "share"

    def autostop_sharing_checkbox_clicked(self):
        """
        Save autostop sharing setting to the tab settings
        """
        self.settings.set(
            "share", "autostop_sharing", self.autostop_sharing_checkbox.isChecked()
        )

    def update_primary_action(self):
        self.common.log("ShareMode", "update_primary_action")

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
