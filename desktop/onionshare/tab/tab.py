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

import queue
from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.onionshare import OnionShare
from onionshare_cli.web import Web
from onionshare_cli.mode_settings import ModeSettings

from .mode.share_mode import ShareMode
from .mode.receive_mode import ReceiveMode
from .mode.website_mode import WebsiteMode
from .mode.chat_mode import ChatMode

from .server_status import ServerStatus

from .. import strings
from ..gui_common import GuiCommon
from ..widgets import Alert


class NewTabButton(QtWidgets.QPushButton):
    def __init__(self, common, image_filename, title, text, shortcut):
        super(NewTabButton, self).__init__()
        self.common = common

        self.setFixedSize(280, 280)

        # Keyboard shortcut, using the first letter of the mode
        sequence = QtGui.QKeySequence(QtCore.Qt.CTRL + shortcut)
        self.setShortcut(sequence)

        self.setAccessibleName(title)

        # Image
        self.image_label = QtWidgets.QLabel(parent=self)
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(GuiCommon.get_resource_path(image_filename))
            )
        )
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet(self.common.gui.css["new_tab_button_image"])
        self.image_label.setGeometry(0, 0, self.width(), 190)
        self.image_label.show()

        # Title
        self.title_label = QtWidgets.QLabel(title, parent=self)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet(self.common.gui.css["new_tab_title_text"])
        if self.title_label.sizeHint().width() >= 250:
            self.title_label.setGeometry(
                (self.width() - 250) / 2, self.height() - 120, 250, 60
            )
        else:
            self.title_label.setGeometry(
                (self.width() - 250) / 2, self.height() - 100, 250, 30
            )
        self.title_label.show()

        # Text
        self.text_label = QtWidgets.QLabel(text, parent=self)
        self.text_label.setAlignment(QtCore.Qt.AlignCenter)
        self.text_label.setStyleSheet(self.common.gui.css["new_tab_button_text"])
        self.text_label.setGeometry(
            (self.width() - 200) / 2, self.height() - 50, 200, 30
        )
        self.text_label.show()


class Tab(QtWidgets.QWidget):
    """
    A GUI tab, you know, sort of like in a web browser
    """

    change_title = QtCore.Signal(int, str)
    change_icon = QtCore.Signal(int, str)
    change_persistent = QtCore.Signal(int, bool)

    def __init__(
        self,
        common,
        tab_id,
        system_tray,
        status_bar,
        filenames=None,
    ):
        super(Tab, self).__init__()
        self.common = common
        self.common.log("Tab", "__init__")

        self.tab_id = tab_id
        self.system_tray = system_tray
        self.status_bar = status_bar
        self.filenames = filenames

        self.mode = None

        # Start the OnionShare app
        self.app = OnionShare(common, self.common.gui.onion, self.common.gui.local_only)

        # An invisible widget, used for hiding the persistent tab icon
        self.invisible_widget = QtWidgets.QWidget()
        self.invisible_widget.setFixedSize(0, 0)

        # Onionshare logo
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(
                        "images/{}_logo_text.png".format(self.common.gui.color_mode)
                    )
                )
            )
        )
        self.image_label.setFixedSize(180, 40)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.image_label)
        image_layout.addStretch()
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # New tab buttons
        self.share_button = NewTabButton(
            self.common,
            "images/{}_mode_new_tab_share.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_share_button"),
            strings._("gui_main_page_share_button"),
            QtCore.Qt.Key_S,
        )
        self.share_button.clicked.connect(self.share_mode_clicked)

        self.receive_button = NewTabButton(
            self.common,
            "images/{}_mode_new_tab_receive.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_receive_button"),
            strings._("gui_main_page_receive_button"),
            QtCore.Qt.Key_R,
        )
        self.receive_button.clicked.connect(self.receive_mode_clicked)

        self.website_button = NewTabButton(
            self.common,
            "images/{}_mode_new_tab_website.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_website_button"),
            strings._("gui_main_page_website_button"),
            QtCore.Qt.Key_W,
        )
        self.website_button.clicked.connect(self.website_mode_clicked)

        self.chat_button = NewTabButton(
            self.common,
            "images/{}_mode_new_tab_chat.png".format(self.common.gui.color_mode),
            strings._("gui_new_tab_chat_button"),
            strings._("gui_main_page_chat_button"),
            QtCore.Qt.Key_C,
        )
        self.chat_button.clicked.connect(self.chat_mode_clicked)

        new_tab_top_layout = QtWidgets.QHBoxLayout()
        new_tab_top_layout.addStretch()
        new_tab_top_layout.addWidget(self.share_button)
        new_tab_top_layout.addWidget(self.receive_button)
        new_tab_top_layout.addStretch()

        new_tab_bottom_layout = QtWidgets.QHBoxLayout()
        new_tab_bottom_layout.addStretch()
        new_tab_bottom_layout.addWidget(self.website_button)
        new_tab_bottom_layout.addWidget(self.chat_button)
        new_tab_bottom_layout.addStretch()

        new_tab_layout = QtWidgets.QVBoxLayout()
        new_tab_layout.addStretch()
        new_tab_layout.addLayout(new_tab_top_layout)
        new_tab_layout.addLayout(new_tab_bottom_layout)
        new_tab_layout.addStretch()

        new_tab_img_layout = QtWidgets.QHBoxLayout()
        new_tab_img_layout.addWidget(self.image)
        new_tab_img_layout.addStretch(1)
        new_tab_img_layout.addLayout(new_tab_layout)
        new_tab_img_layout.addStretch(2)

        self.new_tab = QtWidgets.QWidget()
        self.new_tab.setLayout(new_tab_img_layout)
        self.new_tab.show()

        # Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.new_tab)
        self.setLayout(self.layout)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_callback)

        # Persistent image
        self.persistent_image_label = QtWidgets.QLabel()
        self.persistent_image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path("images/persistent_enabled.png")
                )
            )
        )
        self.persistent_image_label.setFixedSize(20, 20)

        # Create the close warning dialog -- the dialog widget needs to be in the constructor
        # in order to test it
        self.close_dialog = QtWidgets.QMessageBox()
        self.close_dialog.setWindowTitle(strings._("gui_close_tab_warning_title"))
        self.close_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.close_dialog.accept_button = self.close_dialog.addButton(
            strings._("gui_close_tab_warning_close"), QtWidgets.QMessageBox.AcceptRole
        )
        self.close_dialog.reject_button = self.close_dialog.addButton(
            strings._("gui_close_tab_warning_cancel"), QtWidgets.QMessageBox.RejectRole
        )
        self.close_dialog.setDefaultButton(self.close_dialog.reject_button)

    def init(self, mode_settings=None):
        if mode_settings:
            # Load this tab
            self.settings = mode_settings
            mode = self.settings.get("persistent", "mode")
            if mode == "share":
                self.filenames = self.settings.get("share", "filenames")
                self.share_mode_clicked()
            elif mode == "receive":
                self.receive_mode_clicked()
            elif mode == "website":
                self.filenames = self.settings.get("website", "filenames")
                self.website_mode_clicked()
            elif mode == "chat":
                self.chat_mode_clicked()
        else:
            # This is a new tab
            self.settings = ModeSettings(self.common)

    def share_mode_clicked(self):
        self.common.log("Tab", "share_mode_clicked")
        self.mode = self.common.gui.MODE_SHARE
        self.new_tab.hide()

        self.share_mode = ShareMode(self)
        self.share_mode.change_persistent.connect(self.change_persistent)

        self.layout.addWidget(self.share_mode)
        self.share_mode.show()

        self.share_mode.init()
        self.share_mode.server_status.server_started.connect(
            self.update_server_status_indicator
        )
        self.share_mode.server_status.server_stopped.connect(
            self.update_server_status_indicator
        )
        self.share_mode.start_server_finished.connect(
            self.update_server_status_indicator
        )
        self.share_mode.stop_server_finished.connect(
            self.update_server_status_indicator
        )
        self.share_mode.stop_server_finished.connect(self.stop_server_finished)
        self.share_mode.start_server_finished.connect(self.clear_message)
        self.share_mode.server_status.button_clicked.connect(self.clear_message)
        self.share_mode.server_status.url_copied.connect(self.copy_url)
        self.share_mode.server_status.client_auth_copied.connect(self.copy_client_auth)

        self.change_title.emit(self.tab_id, strings._("gui_tab_name_share"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def receive_mode_clicked(self):
        self.common.log("Tab", "receive_mode_clicked")
        self.mode = self.common.gui.MODE_RECEIVE
        self.new_tab.hide()

        self.receive_mode = ReceiveMode(self)
        self.receive_mode.change_persistent.connect(self.change_persistent)

        self.layout.addWidget(self.receive_mode)
        self.receive_mode.show()

        self.receive_mode.init()
        self.receive_mode.server_status.server_started.connect(
            self.update_server_status_indicator
        )
        self.receive_mode.server_status.server_stopped.connect(
            self.update_server_status_indicator
        )
        self.receive_mode.start_server_finished.connect(
            self.update_server_status_indicator
        )
        self.receive_mode.stop_server_finished.connect(
            self.update_server_status_indicator
        )
        self.receive_mode.stop_server_finished.connect(self.stop_server_finished)
        self.receive_mode.start_server_finished.connect(self.clear_message)
        self.receive_mode.server_status.button_clicked.connect(self.clear_message)
        self.receive_mode.server_status.url_copied.connect(self.copy_url)
        self.receive_mode.server_status.client_auth_copied.connect(
            self.copy_client_auth
        )

        self.change_title.emit(self.tab_id, strings._("gui_tab_name_receive"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def website_mode_clicked(self):
        self.common.log("Tab", "website_mode_clicked")
        self.mode = self.common.gui.MODE_WEBSITE
        self.new_tab.hide()

        self.website_mode = WebsiteMode(self)
        self.website_mode.change_persistent.connect(self.change_persistent)

        self.layout.addWidget(self.website_mode)
        self.website_mode.show()

        self.website_mode.init()
        self.website_mode.server_status.server_started.connect(
            self.update_server_status_indicator
        )
        self.website_mode.server_status.server_stopped.connect(
            self.update_server_status_indicator
        )
        self.website_mode.start_server_finished.connect(
            self.update_server_status_indicator
        )
        self.website_mode.stop_server_finished.connect(
            self.update_server_status_indicator
        )
        self.website_mode.stop_server_finished.connect(self.stop_server_finished)
        self.website_mode.start_server_finished.connect(self.clear_message)
        self.website_mode.server_status.button_clicked.connect(self.clear_message)
        self.website_mode.server_status.url_copied.connect(self.copy_url)
        self.website_mode.server_status.client_auth_copied.connect(
            self.copy_client_auth
        )

        self.change_title.emit(self.tab_id, strings._("gui_tab_name_website"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def chat_mode_clicked(self):
        self.common.log("Tab", "chat_mode_clicked")
        self.mode = self.common.gui.MODE_CHAT
        self.new_tab.hide()

        self.chat_mode = ChatMode(self)
        self.chat_mode.change_persistent.connect(self.change_persistent)

        self.layout.addWidget(self.chat_mode)
        self.chat_mode.show()

        self.chat_mode.init()
        self.chat_mode.server_status.server_started.connect(
            self.update_server_status_indicator
        )
        self.chat_mode.server_status.server_stopped.connect(
            self.update_server_status_indicator
        )
        self.chat_mode.start_server_finished.connect(
            self.update_server_status_indicator
        )
        self.chat_mode.stop_server_finished.connect(self.update_server_status_indicator)
        self.chat_mode.stop_server_finished.connect(self.stop_server_finished)
        self.chat_mode.start_server_finished.connect(self.clear_message)
        self.chat_mode.server_status.button_clicked.connect(self.clear_message)
        self.chat_mode.server_status.url_copied.connect(self.copy_url)
        self.chat_mode.server_status.client_auth_copied.connect(self.copy_client_auth)

        self.change_title.emit(self.tab_id, strings._("gui_tab_name_chat"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def update_server_status_indicator(self):
        # Set the status image
        if self.mode == self.common.gui.MODE_SHARE:
            # Share mode
            if self.share_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.set_server_status_indicator_stopped(
                    strings._("gui_status_indicator_share_stopped")
                )
            elif self.share_mode.server_status.status == ServerStatus.STATUS_WORKING:
                if self.settings.get("general", "autostart_timer"):
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_share_scheduled")
                    )
                else:
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_share_working")
                    )
            elif self.share_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.set_server_status_indicator_started(
                    strings._("gui_status_indicator_share_started")
                )
        elif self.mode == self.common.gui.MODE_WEBSITE:
            # Website mode
            if self.website_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.set_server_status_indicator_stopped(
                    strings._("gui_status_indicator_share_stopped")
                )
            elif self.website_mode.server_status.status == ServerStatus.STATUS_WORKING:
                if self.website_mode.server_status.autostart_timer_datetime:
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_share_scheduled")
                    )
                else:
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_share_working")
                    )
            elif self.website_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.set_server_status_indicator_started(
                    strings._("gui_status_indicator_share_started")
                )
        elif self.mode == self.common.gui.MODE_RECEIVE:
            # Receive mode
            if self.receive_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.set_server_status_indicator_stopped(
                    strings._("gui_status_indicator_receive_stopped")
                )
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_WORKING:
                if self.settings.get("general", "autostart_timer"):
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_receive_scheduled")
                    )
                else:
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_receive_working")
                    )
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.set_server_status_indicator_started(
                    strings._("gui_status_indicator_receive_started")
                )
        elif self.mode == self.common.gui.MODE_CHAT:
            # Chat mode
            if self.chat_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.set_server_status_indicator_stopped(
                    strings._("gui_status_indicator_chat_stopped")
                )
            elif self.chat_mode.server_status.status == ServerStatus.STATUS_WORKING:
                if self.settings.get("general", "autostart_timer"):
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_chat_scheduled")
                    )
                else:
                    self.set_server_status_indicator_working(
                        strings._("gui_status_indicator_chat_working")
                    )
            elif self.chat_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.set_server_status_indicator_started(
                    strings._("gui_status_indicator_chat_started")
                )

    def set_server_status_indicator_stopped(self, label_text):
        self.change_icon.emit(self.tab_id, "images/server_stopped.png")
        self.status_bar.server_status_image_label.setPixmap(
            QtGui.QPixmap.fromImage(self.status_bar.server_status_image_stopped)
        )
        self.status_bar.server_status_label.setText(label_text)

    def set_server_status_indicator_working(self, label_text):
        self.change_icon.emit(self.tab_id, "images/server_working.png")
        self.status_bar.server_status_image_label.setPixmap(
            QtGui.QPixmap.fromImage(self.status_bar.server_status_image_working)
        )
        self.status_bar.server_status_label.setText(label_text)

    def set_server_status_indicator_started(self, label_text):
        self.change_icon.emit(self.tab_id, "images/server_started.png")
        self.status_bar.server_status_image_label.setPixmap(
            QtGui.QPixmap.fromImage(self.status_bar.server_status_image_started)
        )
        self.status_bar.server_status_label.setText(label_text)

    def stop_server_finished(self):
        # When the server stopped, cleanup the ephemeral onion service
        self.get_mode().app.stop_onion_service(self.settings)

    def timer_callback(self):
        """
        Check for messages communicated from the web app, and update the GUI accordingly. Also,
        call ShareMode and ReceiveMode's timer_callbacks.
        """
        self.update()

        if not self.common.gui.local_only:
            # Have we lost connection to Tor somehow?
            if not self.common.gui.onion.is_authenticated():
                self.timer.stop()
                self.status_bar.showMessage(strings._("gui_tor_connection_lost"))
                self.system_tray.showMessage(
                    strings._("gui_tor_connection_lost"),
                    strings._("gui_tor_connection_error_settings"),
                )
                self.get_mode().handle_tor_broke()

        # Process events from the web object
        mode = self.get_mode()

        events = []

        done = False
        while not done:
            try:
                r = mode.web.q.get(False)
                events.append(r)
            except queue.Empty:
                done = True

        for event in events:
            if event["type"] == Web.REQUEST_LOAD:
                mode.handle_request_load(event)

            elif event["type"] == Web.REQUEST_STARTED:
                mode.handle_request_started(event)

            elif event["type"] == Web.REQUEST_PROGRESS:
                mode.handle_request_progress(event)

            elif event["type"] == Web.REQUEST_CANCELED:
                mode.handle_request_canceled(event)

            elif event["type"] == Web.REQUEST_UPLOAD_INCLUDES_MESSAGE:
                mode.handle_request_upload_includes_message(event)

            elif event["type"] == Web.REQUEST_UPLOAD_FILE_RENAMED:
                mode.handle_request_upload_file_renamed(event)

            elif event["type"] == Web.REQUEST_UPLOAD_SET_DIR:
                mode.handle_request_upload_set_dir(event)

            elif event["type"] == Web.REQUEST_UPLOAD_FINISHED:
                mode.handle_request_upload_finished(event)

            elif event["type"] == Web.REQUEST_UPLOAD_CANCELED:
                mode.handle_request_upload_canceled(event)

            elif event["type"] == Web.REQUEST_INDIVIDUAL_FILE_STARTED:
                mode.handle_request_individual_file_started(event)

            elif event["type"] == Web.REQUEST_INDIVIDUAL_FILE_PROGRESS:
                mode.handle_request_individual_file_progress(event)

            elif event["type"] == Web.REQUEST_INDIVIDUAL_FILE_CANCELED:
                mode.handle_request_individual_file_canceled(event)

            if event["type"] == Web.REQUEST_ERROR_DATA_DIR_CANNOT_CREATE:
                Alert(
                    self.common,
                    strings._("error_cannot_create_data_dir").format(
                        event["data"]["receive_mode_dir"]
                    ),
                )

            if event["type"] == Web.REQUEST_OTHER:
                if (
                    event["path"] != "/favicon.ico"
                    and event["path"] != f"/{mode.web.shutdown_password}/shutdown"
                ):
                    self.status_bar.showMessage(
                        f"{strings._('other_page_loaded')}: {event['path']}"
                    )

        mode.timer_callback()

    def copy_url(self):
        """
        When the URL gets copied to the clipboard, display this in the status bar.
        """
        self.common.log("Tab", "copy_url")
        self.system_tray.showMessage(
            strings._("gui_copied_url_title"), strings._("gui_copied_url")
        )

    def copy_client_auth(self):
        """
        When the onion service's ClientAuth private key gets copied to
        the clipboard, display this in the status bar.
        """
        self.common.log("Tab", "copy_client_auth")
        self.system_tray.showMessage(
            strings._("gui_copied_client_auth_title"),
            strings._("gui_copied_client_auth"),
        )

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def get_mode(self):
        if self.mode:
            if self.mode == self.common.gui.MODE_SHARE:
                return self.share_mode
            elif self.mode == self.common.gui.MODE_RECEIVE:
                return self.receive_mode
            elif self.mode == self.common.gui.MODE_CHAT:
                return self.chat_mode
            else:
                return self.website_mode
        else:
            return None

    def settings_have_changed(self):
        # Global settings have changed
        self.common.log("Tab", "settings_have_changed")

        # We might've stopped the main requests timer if a Tor connection failed. If we've reloaded
        # settings, we probably succeeded in obtaining a new connection. If so, restart the timer.
        if not self.common.gui.local_only:
            if self.common.gui.onion.is_authenticated():
                mode = self.get_mode()
                if mode:
                    if not self.timer.isActive():
                        self.timer.start(500)
                    mode.on_reload_settings()

    def close_tab(self):
        self.common.log("Tab", "close_tab")
        if self.mode is None:
            return True

        if self.settings.get("persistent", "enabled"):
            dialog_text = strings._("gui_close_tab_warning_persistent_description")
        else:
            server_status = self.get_mode().server_status
            if server_status.status == server_status.STATUS_STOPPED:
                return True
            else:
                if self.mode == self.common.gui.MODE_SHARE:
                    dialog_text = strings._("gui_close_tab_warning_share_description")
                elif self.mode == self.common.gui.MODE_RECEIVE:
                    dialog_text = strings._("gui_close_tab_warning_receive_description")
                else:
                    dialog_text = strings._("gui_close_tab_warning_website_description")

        # Open the warning dialog
        self.common.log("Tab", "close_tab, opening warning dialog")
        self.close_dialog.setText(dialog_text)
        self.close_dialog.exec_()

        # Close
        if self.close_dialog.clickedButton() == self.close_dialog.accept_button:
            return True
        # Cancel
        else:
            self.common.log("Tab", "close_tab", "cancel, keeping tab open")
            return False

    def cleanup(self):
        self.common.log("Tab", "cleanup", f"tab_id={self.tab_id}")
        if self.get_mode():
            if self.get_mode().web_thread:
                self.get_mode().web.stop(self.get_mode().app.port)
                self.get_mode().web_thread.quit()
                self.get_mode().web_thread.wait()

            self.get_mode().web.cleanup()
