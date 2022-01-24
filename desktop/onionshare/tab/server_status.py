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
import textwrap
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt

from .. import strings
from ..widgets import Alert
from ..widgets import QRCodeDialog
from ..gui_common import GuiCommon


class ServerStatus(QtWidgets.QWidget):
    """
    The server status chunk of the GUI.
    """

    server_started = QtCore.Signal()
    server_started_finished = QtCore.Signal()
    server_stopped = QtCore.Signal()
    server_canceled = QtCore.Signal()
    button_clicked = QtCore.Signal()
    url_copied = QtCore.Signal()
    client_auth_copied = QtCore.Signal()

    STATUS_STOPPED = 0
    STATUS_WORKING = 1
    STATUS_STARTED = 2

    def __init__(
        self,
        common,
        qtapp,
        app,
        mode_settings,
        mode_settings_widget,
        file_selection=None,
        local_only=False,
    ):
        super(ServerStatus, self).__init__()

        self.common = common

        self.status = self.STATUS_STOPPED
        self.mode = None  # Gets set in self.set_mode

        self.qtapp = qtapp
        self.app = app
        self.settings = mode_settings
        self.mode_settings_widget = mode_settings_widget

        self.web = None
        self.autostart_timer_datetime = None
        self.local_only = local_only

        self.resizeEvent(None)

        # Server layout
        self.server_button = QtWidgets.QPushButton()
        self.server_button.clicked.connect(self.server_button_clicked)

        # URL layout
        url_font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.url_description = QtWidgets.QLabel()
        self.url_description.setWordWrap(True)
        self.url_description.setMinimumHeight(50)

        # URL sharing instructions, above the URL and Copy Address/QR Code buttons
        self.url_instructions = QtWidgets.QLabel()
        self.url_instructions.setWordWrap(True)

        # The URL label itself
        self.url = QtWidgets.QLabel()
        self.url.setFont(url_font)
        self.url.setWordWrap(True)
        self.url.setMinimumSize(self.url.sizeHint())
        self.url.setStyleSheet(self.common.gui.css["server_status_url"])
        self.url.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )

        # Copy Onion Address button
        self.copy_url_button = QtWidgets.QPushButton(strings._("gui_copy_url"))
        self.copy_url_button.setStyleSheet(
            self.common.gui.css["server_status_url_buttons"]
        )
        self.copy_url_button.clicked.connect(self.copy_url)

        # Onion Address QR code button
        self.show_url_qr_code_button = QtWidgets.QPushButton(
            strings._("gui_show_qr_code")
        )
        self.show_url_qr_code_button.hide()
        self.show_url_qr_code_button.clicked.connect(
            self.show_url_qr_code_button_clicked
        )
        self.show_url_qr_code_button.setStyleSheet(
            self.common.gui.css["server_status_url_buttons"]
        )

        # Client Auth sharing instructions, above the
        # Copy Private Key/QR Code buttons
        self.client_auth_instructions = QtWidgets.QLabel()
        self.client_auth_instructions.setWordWrap(True)
        self.client_auth_instructions.setText(strings._("gui_client_auth_instructions"))

        # The private key itself
        self.private_key = QtWidgets.QLabel()
        self.private_key.setFont(url_font)
        self.private_key.setWordWrap(True)
        self.private_key.setMinimumSize(self.private_key.sizeHint())
        self.private_key.setStyleSheet(self.common.gui.css["server_status_url"])
        self.private_key.setTextInteractionFlags(Qt.NoTextInteraction)
        self.private_key_hidden = True

        # Copy ClientAuth button
        self.copy_client_auth_button = QtWidgets.QPushButton(
            strings._("gui_copy_client_auth")
        )
        self.copy_client_auth_button.setStyleSheet(
            self.common.gui.css["server_status_url_buttons"]
        )
        self.copy_client_auth_button.clicked.connect(self.copy_client_auth)

        # ClientAuth QR code button
        self.show_client_auth_qr_code_button = QtWidgets.QPushButton(
            strings._("gui_show_qr_code")
        )
        self.show_client_auth_qr_code_button.hide()
        self.show_client_auth_qr_code_button.clicked.connect(
            self.show_client_auth_qr_code_button_clicked
        )
        self.show_client_auth_qr_code_button.setStyleSheet(
            self.common.gui.css["server_status_url_buttons"]
        )

        # ClientAuth reveal/hide toggle button
        self.client_auth_toggle_button = QtWidgets.QPushButton(strings._("gui_reveal"))
        self.client_auth_toggle_button.hide()
        self.client_auth_toggle_button.clicked.connect(
            self.client_auth_toggle_button_clicked
        )
        self.client_auth_toggle_button.setStyleSheet(
            self.common.gui.css["server_status_url_buttons"]
        )

        # URL instructions layout
        url_buttons_layout = QtWidgets.QHBoxLayout()
        url_buttons_layout.addWidget(self.copy_url_button)
        url_buttons_layout.addWidget(self.show_url_qr_code_button)
        url_buttons_layout.addStretch()

        url_layout = QtWidgets.QVBoxLayout()
        url_layout.addWidget(self.url_description)
        url_layout.addWidget(self.url_instructions)
        url_layout.addWidget(self.url)
        url_layout.addLayout(url_buttons_layout)

        # Private key instructions layout
        client_auth_buttons_layout = QtWidgets.QHBoxLayout()
        client_auth_buttons_layout.addWidget(self.copy_client_auth_button)
        client_auth_buttons_layout.addWidget(self.show_client_auth_qr_code_button)
        client_auth_buttons_layout.addWidget(self.client_auth_toggle_button)
        client_auth_buttons_layout.addStretch()

        client_auth_layout = QtWidgets.QVBoxLayout()
        client_auth_layout.addWidget(self.client_auth_instructions)
        client_auth_layout.addWidget(self.private_key)
        client_auth_layout.addLayout(client_auth_buttons_layout)

        # Add the widgets and URL/ClientAuth layouts
        # to the main ServerStatus layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.server_button)
        button_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addLayout(url_layout)
        layout.addLayout(client_auth_layout)
        self.setLayout(layout)

    def set_mode(self, share_mode, file_selection=None):
        """
        The server status is in share mode.
        """
        self.mode = share_mode

        if (self.mode == self.common.gui.MODE_SHARE) or (
            self.mode == self.common.gui.MODE_WEBSITE
        ):
            self.file_selection = file_selection

        self.update()

    def resizeEvent(self, event):
        """
        When the widget is resized, try and adjust the display of a v3 onion URL.
        """
        try:
            # Wrap the URL label
            url_length = len(self.get_url())
            if url_length > 60:
                width = self.frameGeometry().width()
                if width < 530:
                    wrapped_onion_url = textwrap.fill(self.get_url(), 46)
                    self.url.setText(wrapped_onion_url)
                else:
                    self.url.setText(self.get_url())
        except Exception:
            pass

    def show_url(self):
        """
        Show the URL in the UI.
        """
        self.url_description.show()

        info_image = GuiCommon.get_resource_path("images/info.png")

        if self.mode == self.common.gui.MODE_SHARE:
            if self.settings.get("general", "public"):
                self.url_description.setText(
                    strings._("gui_share_url_public_description").format(info_image)
                )
            else:
                self.url_description.setText(
                    strings._("gui_share_url_description").format(info_image)
                )
        elif self.mode == self.common.gui.MODE_WEBSITE:
            if self.settings.get("general", "public"):
                self.url_description.setText(
                    strings._("gui_website_url_public_description").format(info_image)
                )
            else:
                self.url_description.setText(
                    strings._("gui_website_url_description").format(info_image)
                )
        elif self.mode == self.common.gui.MODE_RECEIVE:
            if self.settings.get("general", "public"):
                self.url_description.setText(
                    strings._("gui_receive_url_public_description").format(info_image)
                )
            else:
                self.url_description.setText(
                    strings._("gui_receive_url_description").format(info_image)
                )
        elif self.mode == self.common.gui.MODE_CHAT:
            if self.settings.get("general", "public"):
                self.url_description.setText(
                    strings._("gui_chat_url_public_description").format(info_image)
                )
            else:
                self.url_description.setText(
                    strings._("gui_chat_url_description").format(info_image)
                )

        # Show a Tool Tip explaining the lifecycle of this URL
        if self.settings.get("persistent", "enabled"):
            if self.mode == self.common.gui.MODE_SHARE and self.settings.get(
                "share", "autostop_sharing"
            ):
                self.url_description.setToolTip(
                    strings._("gui_url_label_onetime_and_persistent")
                )
            else:
                self.url_description.setToolTip(strings._("gui_url_label_persistent"))
        else:
            if self.mode == self.common.gui.MODE_SHARE and self.settings.get(
                "share", "autostop_sharing"
            ):
                self.url_description.setToolTip(strings._("gui_url_label_onetime"))
            else:
                self.url_description.setToolTip(strings._("gui_url_label_stay_open"))

        if self.settings.get("general", "public"):
            self.url_instructions.setText(strings._("gui_url_instructions_public_mode"))
        else:
            self.url_instructions.setText(strings._("gui_url_instructions"))
        self.url_instructions.show()
        self.url.setText(self.get_url())
        self.url.show()
        self.copy_url_button.show()
        self.show_url_qr_code_button.show()

        if self.settings.get("general", "public"):
            self.client_auth_instructions.hide()
            self.private_key.hide()
            self.copy_client_auth_button.hide()
            self.show_client_auth_qr_code_button.hide()
        else:
            self.client_auth_instructions.show()
            if self.private_key_hidden:
                self.private_key.setText("*" * len(self.app.auth_string))
                self.private_key.setTextInteractionFlags(Qt.NoTextInteraction)
            else:
                self.private_key.setText(self.app.auth_string)
                self.private_key.setTextInteractionFlags(
                    Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
                )
            self.private_key.show()
            self.copy_client_auth_button.show()
            self.show_client_auth_qr_code_button.show()
            self.client_auth_toggle_button.show()

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        self.common.log("ServerStatus", "update")
        # Set the URL fields
        if self.status == self.STATUS_STARTED:
            # The backend Onion may have saved new settings, such as the private key.
            # Reload the settings before saving new ones.
            self.common.settings.load()
            self.show_url()

            if self.settings.get("general", "autostop_timer"):
                self.server_button.setToolTip(
                    strings._("gui_stop_server_autostop_timer_tooltip").format(
                        self.mode_settings_widget.autostop_timer_widget.dateTime().toString(
                            "h:mm AP, MMMM dd, yyyy"
                        )
                    )
                )
        else:
            self.url_description.hide()
            self.url_instructions.hide()
            self.url.hide()
            self.copy_url_button.hide()
            self.show_url_qr_code_button.hide()
            self.private_key.hide()
            self.client_auth_instructions.hide()
            self.copy_client_auth_button.hide()
            self.show_client_auth_qr_code_button.hide()
            self.client_auth_toggle_button.hide()

            self.mode_settings_widget.update_ui()

        # Button
        if (
            self.mode == self.common.gui.MODE_SHARE
            and self.file_selection.get_num_files() == 0
        ):
            self.server_button.hide()
        elif (
            self.mode == self.common.gui.MODE_WEBSITE
            and self.file_selection.get_num_files() == 0
        ):
            self.server_button.hide()
        else:
            self.server_button.show()

            if self.status == self.STATUS_STOPPED:
                self.server_button.setStyleSheet(
                    self.common.gui.css["server_status_button_stopped"]
                )
                self.server_button.setEnabled(True)
                if self.mode == self.common.gui.MODE_SHARE:
                    self.server_button.setText(strings._("gui_share_start_server"))
                elif self.mode == self.common.gui.MODE_WEBSITE:
                    self.server_button.setText(strings._("gui_share_start_server"))
                elif self.mode == self.common.gui.MODE_CHAT:
                    self.server_button.setText(strings._("gui_chat_start_server"))
                else:
                    self.server_button.setText(strings._("gui_receive_start_server"))
                self.server_button.setToolTip("")
            elif self.status == self.STATUS_STARTED:
                self.server_button.setStyleSheet(
                    self.common.gui.css["server_status_button_started"]
                )
                self.server_button.setEnabled(True)
                if self.mode == self.common.gui.MODE_SHARE:
                    self.server_button.setText(strings._("gui_share_stop_server"))
                elif self.mode == self.common.gui.MODE_WEBSITE:
                    self.server_button.setText(strings._("gui_share_stop_server"))
                elif self.mode == self.common.gui.MODE_CHAT:
                    self.server_button.setText(strings._("gui_chat_stop_server"))
                else:
                    self.server_button.setText(strings._("gui_receive_stop_server"))
            elif self.status == self.STATUS_WORKING:
                self.server_button.setStyleSheet(
                    self.common.gui.css["server_status_button_working"]
                )
                self.server_button.setEnabled(True)
                if self.settings.get("general", "autostart_timer"):
                    self.server_button.setToolTip(
                        strings._("gui_start_server_autostart_timer_tooltip").format(
                            self.mode_settings_widget.autostart_timer_widget.dateTime().toString(
                                "h:mm AP, MMMM dd, yyyy"
                            )
                        )
                    )
                else:
                    if self.common.platform == "Windows":
                        self.server_button.setText(strings._("gui_please_wait"))
                    else:
                        self.server_button.setText(
                            strings._("gui_please_wait_no_button")
                        )
            else:
                self.server_button.setStyleSheet(
                    self.common.gui.css["server_status_button_working"]
                )
                self.server_button.setEnabled(False)
                self.server_button.setText(strings._("gui_please_wait_no_button"))

    def server_button_clicked(self):
        """
        Toggle starting or stopping the server.
        """
        if self.status == self.STATUS_STOPPED:
            can_start = True
            if self.settings.get("general", "autostart_timer"):
                if self.local_only:
                    self.autostart_timer_datetime = (
                        self.mode_settings_widget.autostart_timer_widget.dateTime().toPython()
                    )
                else:
                    self.autostart_timer_datetime = (
                        self.mode_settings_widget.autostart_timer_widget.dateTime()
                        .toPython()
                        .replace(second=0, microsecond=0)
                    )
                # If the timer has actually passed already before the user hit Start, refuse to start the server.
                if (
                    QtCore.QDateTime.currentDateTime().toPython()
                    > self.autostart_timer_datetime
                ):
                    can_start = False
                    Alert(
                        self.common,
                        strings._("gui_server_autostart_timer_expired"),
                        QtWidgets.QMessageBox.Warning,
                    )
            if self.settings.get("general", "autostop_timer"):
                if self.local_only:
                    self.autostop_timer_datetime = (
                        self.mode_settings_widget.autostop_timer_widget.dateTime().toPython()
                    )
                else:
                    # Get the timer chosen, stripped of its seconds. This prevents confusion if the share stops at (say) 37 seconds past the minute chosen
                    self.autostop_timer_datetime = (
                        self.mode_settings_widget.autostop_timer_widget.dateTime()
                        .toPython()
                        .replace(second=0, microsecond=0)
                    )
                # If the timer has actually passed already before the user hit Start, refuse to start the server.
                if (
                    QtCore.QDateTime.currentDateTime().toPython()
                    > self.autostop_timer_datetime
                ):
                    can_start = False
                    Alert(
                        self.common,
                        strings._("gui_server_autostop_timer_expired"),
                        QtWidgets.QMessageBox.Warning,
                    )
                if self.settings.get("general", "autostart_timer"):
                    if self.autostop_timer_datetime <= self.autostart_timer_datetime:
                        Alert(
                            self.common,
                            strings._(
                                "gui_autostop_timer_cant_be_earlier_than_autostart_timer"
                            ),
                            QtWidgets.QMessageBox.Warning,
                        )
                        can_start = False
            if can_start:
                self.start_server()
        elif self.status == self.STATUS_STARTED:
            self.stop_server()
        elif self.status == self.STATUS_WORKING and (
            self.common.platform == "Windows"
            or self.settings.get("general", "autostart_timer")
        ):
            self.cancel_server()
        self.button_clicked.emit()

    def show_url_qr_code_button_clicked(self):
        """
        Show a QR code of the onion URL.
        """
        self.qr_code_dialog = QRCodeDialog(
            self.common, strings._("gui_qr_label_url_title"), self.get_url()
        )

    def show_client_auth_qr_code_button_clicked(self):
        """
        Show a QR code of the private key
        """
        self.qr_code_dialog = QRCodeDialog(
            self.common,
            strings._("gui_qr_label_auth_string_title"),
            self.app.auth_string,
        )

    def client_auth_toggle_button_clicked(self):
        """
        ClientAuth reveal/hide toggle button clicked
        """
        if self.private_key_hidden:
            self.private_key_hidden = False
            self.client_auth_toggle_button.setText(strings._("gui_hide"))
        else:
            self.private_key_hidden = True
            self.client_auth_toggle_button.setText(strings._("gui_reveal"))

        self.show_url()

    def start_server(self):
        """
        Start the server.
        """
        self.status = self.STATUS_WORKING
        self.update()
        self.server_started.emit()

    def start_server_finished(self):
        """
        The server has finished starting.
        """
        self.status = self.STATUS_STARTED
        # self.copy_url()
        self.update()
        self.server_started_finished.emit()

    def stop_server(self):
        """
        Stop the server.
        """
        self.status = self.STATUS_WORKING
        self.mode_settings_widget.autostart_timer_reset()
        self.mode_settings_widget.autostop_timer_reset()
        self.update()
        self.server_stopped.emit()

    def cancel_server(self):
        """
        Cancel the server.
        """
        self.common.log(
            "ServerStatus", "cancel_server", "Canceling the server mid-startup"
        )
        self.status = self.STATUS_WORKING
        self.mode_settings_widget.autostart_timer_reset()
        self.mode_settings_widget.autostop_timer_reset()
        self.update()
        self.server_canceled.emit()

    def stop_server_finished(self):
        """
        The server has finished stopping.
        """
        self.status = self.STATUS_STOPPED
        self.update()

    def copy_url(self):
        """
        Copy the onionshare URL to the clipboard.
        """
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.get_url())

        self.url_copied.emit()

    def copy_client_auth(self):
        """
        Copy the ClientAuth private key line to the clipboard.
        """
        clipboard = self.qtapp.clipboard()
        clipboard.setText(self.app.auth_string)

        self.client_auth_copied.emit()

    def get_url(self):
        """
        Returns the OnionShare URL.
        """
        url = f"http://{self.app.onion_host}"
        return url
