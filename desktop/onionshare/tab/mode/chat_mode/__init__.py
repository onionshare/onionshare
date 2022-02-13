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

from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.web import Web

from .. import Mode
from .... import strings
from ....widgets import MinimumSizeWidget
from ....gui_common import GuiCommon


class ChatMode(Mode):
    """
    Parts of the main window UI for sharing files.
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def init(self):
        """
        Custom initialization for ChatMode.
        """
        # Create the Web object
        self.web = Web(self.common, True, self.settings, "chat")

        # Chat image
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(
                        "images/{}_mode_chat.png".format(self.common.gui.color_mode)
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

        # Set title placeholder
        self.mode_settings_widget.title_lineedit.setPlaceholderText(
            strings._("gui_tab_name_chat")
        )

        # Server status
        self.server_status.set_mode("chat")
        self.server_status.server_started_finished.connect(self.update_primary_action)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.update_primary_action)
        # Tell server_status about web, then update
        self.server_status.web = self.web
        self.server_status.update()

        # Header
        header_label = QtWidgets.QLabel(strings._("gui_new_tab_chat_button"))
        header_label.setStyleSheet(self.common.gui.css["mode_header_label"])

        # Top bar
        top_bar_layout = QtWidgets.QHBoxLayout()
        # Add space at the top, same height as the toggle history bar in other modes
        top_bar_layout.addWidget(MinimumSizeWidget(0, 30))

        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addWidget(header_label)
        self.main_layout.addWidget(self.primary_action, stretch=1)
        self.main_layout.addWidget(self.server_status)
        self.main_layout.addWidget(MinimumSizeWidget(700, 0))

        # Column layout
        self.column_layout = QtWidgets.QHBoxLayout()
        self.column_layout.addWidget(self.image)
        self.column_layout.addLayout(self.main_layout)

        # Content layout
        self.content_layout.addLayout(self.column_layout)

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        return "chat"

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
        self.web.chat_mode.cur_history_id = 0

    def start_server_step2_custom(self):
        """
        Step 2 in starting the server. Zipping up files.
        """
        # Continue
        self.starting_server_step3.emit()
        self.start_server_finished.emit()

    def cancel_server_custom(self):
        """
        Log that the server has been cancelled
        """
        self.common.log("ChatMode", "cancel_server")

    def handle_tor_broke_custom(self):
        """
        Connection to Tor broke.
        """
        self.primary_action.hide()

    def on_reload_settings(self):
        """
        We should be ok to re-enable the 'Start Receive Mode' button now.
        """
        self.primary_action.show()

    def update_primary_action(self):
        self.common.log("ChatMode", "update_primary_action")
