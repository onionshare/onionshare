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
import queue
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.onionshare import OnionShare
from onionshare.web import Web
from onionshare.mode_settings import ModeSettings

from .mode.share_mode import ShareMode
from .mode.receive_mode import ReceiveMode
from .mode.website_mode import WebsiteMode

from .server_status import ServerStatus

from ..widgets import Alert


class Tab(QtWidgets.QWidget):
    """
    A GUI tab, you know, sort of like in a web browser
    """

    change_title = QtCore.pyqtSignal(int, str)
    change_icon = QtCore.pyqtSignal(int, str)
    change_persistent = QtCore.pyqtSignal(int, bool)

    def __init__(
        self,
        common,
        tab_id,
        system_tray,
        status_bar,
        mode_settings=None,
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

        # Widgets to display on a new tab
        self.share_button = QtWidgets.QPushButton(strings._("gui_new_tab_share_button"))
        self.share_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        share_description = QtWidgets.QLabel(strings._("gui_new_tab_share_description"))
        share_description.setWordWrap(True)
        self.share_button.clicked.connect(self.share_mode_clicked)

        self.receive_button = QtWidgets.QPushButton(
            strings._("gui_new_tab_receive_button")
        )
        self.receive_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        self.receive_button.clicked.connect(self.receive_mode_clicked)
        receive_description = QtWidgets.QLabel(
            strings._("gui_new_tab_receive_description")
        )
        receive_description.setWordWrap(True)

        self.website_button = QtWidgets.QPushButton(
            strings._("gui_new_tab_website_button")
        )
        self.website_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        self.website_button.clicked.connect(self.website_mode_clicked)
        website_description = QtWidgets.QLabel(
            strings._("gui_new_tab_website_description")
        )
        website_description.setWordWrap(True)

        new_tab_layout = QtWidgets.QVBoxLayout()
        new_tab_layout.addStretch(1)
        new_tab_layout.addWidget(self.share_button)
        new_tab_layout.addWidget(share_description)
        new_tab_layout.addSpacing(50)
        new_tab_layout.addWidget(self.receive_button)
        new_tab_layout.addWidget(receive_description)
        new_tab_layout.addSpacing(50)
        new_tab_layout.addWidget(self.website_button)
        new_tab_layout.addWidget(website_description)
        new_tab_layout.addStretch(3)

        new_tab_inner = QtWidgets.QWidget()
        new_tab_inner.setFixedWidth(500)
        new_tab_inner.setLayout(new_tab_layout)

        new_tab_outer_layout = QtWidgets.QHBoxLayout()
        new_tab_outer_layout.addStretch()
        new_tab_outer_layout.addWidget(new_tab_inner)
        new_tab_outer_layout.addStretch()

        self.new_tab = QtWidgets.QWidget()
        self.new_tab.setLayout(new_tab_outer_layout)
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
                    self.common.get_resource_path("images/persistent_enabled.png")
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
        self.share_mode.server_status.hidservauth_copied.connect(self.copy_hidservauth)

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_share_button"))

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
        self.receive_mode.server_status.hidservauth_copied.connect(
            self.copy_hidservauth
        )

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_receive_button"))

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
        self.website_mode.server_status.hidservauth_copied.connect(
            self.copy_hidservauth
        )

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_website_button"))

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
                if self.share_mode.server_status.autostart_timer_datetime:
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
                if self.receive_mode.server_status.autostart_timer_datetime:
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

            elif event["type"] == Web.REQUEST_RATE_LIMIT:
                mode.handle_request_rate_limit(event)

            elif event["type"] == Web.REQUEST_PROGRESS:
                mode.handle_request_progress(event)

            elif event["type"] == Web.REQUEST_CANCELED:
                mode.handle_request_canceled(event)

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

            if event["type"] == Web.REQUEST_INVALID_PASSWORD:
                self.status_bar.showMessage(
                    f"[#{mode.web.invalid_passwords_count}] {strings._('incorrect_password')}: {event['data']}"
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

    def copy_hidservauth(self):
        """
        When the stealth onion service HidServAuth gets copied to the clipboard, display this in the status bar.
        """
        self.common.log("Tab", "copy_hidservauth")
        self.system_tray.showMessage(
            strings._("gui_copied_hidservauth_title"),
            strings._("gui_copied_hidservauth"),
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
            self.common.log("Tab", "close_tab", "close, closing tab")
            self.get_mode().stop_server()
            self.app.cleanup()
            return True
        # Cancel
        else:
            self.common.log("Tab", "close_tab", "cancel, keeping tab open")
            return False

    def cleanup(self):
        self.app.cleanup()
