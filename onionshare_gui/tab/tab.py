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

    def __init__(self, common, tab_id, system_tray, status_bar, filenames=None):
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

        # New tab widget
        share_button = QtWidgets.QPushButton(strings._("gui_new_tab_share_button"))
        share_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        share_description = QtWidgets.QLabel(strings._("gui_new_tab_share_description"))
        share_description.setWordWrap(True)
        share_button.clicked.connect(self.share_mode_clicked)

        receive_button = QtWidgets.QPushButton(strings._("gui_new_tab_receive_button"))
        receive_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        receive_button.clicked.connect(self.receive_mode_clicked)
        receive_description = QtWidgets.QLabel(
            strings._("gui_new_tab_receive_description")
        )
        receive_description.setWordWrap(True)

        website_button = QtWidgets.QPushButton(strings._("gui_new_tab_website_button"))
        website_button.setStyleSheet(self.common.gui.css["mode_new_tab_button"])
        website_button.clicked.connect(self.website_mode_clicked)
        website_description = QtWidgets.QLabel(
            strings._("gui_new_tab_website_description")
        )
        website_description.setWordWrap(True)

        new_tab_layout = QtWidgets.QVBoxLayout()
        new_tab_layout.addStretch(1)
        new_tab_layout.addWidget(share_button)
        new_tab_layout.addWidget(share_description)
        new_tab_layout.addSpacing(50)
        new_tab_layout.addWidget(receive_button)
        new_tab_layout.addWidget(receive_description)
        new_tab_layout.addSpacing(50)
        new_tab_layout.addWidget(website_button)
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

        # The server isn't active yet
        self.set_server_active(False)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_callback)

        # Settings for this tab
        self.tab_settings = {"persistence": False}

        # Persistence button
        self.persistence_button = QtWidgets.QPushButton()
        self.persistence_button.setDefault(False)
        self.persistence_button.setFlat(True)
        self.persistence_button.setFixedSize(30, 30)
        self.persistence_button.clicked.connect(self.persistence_button_clicked)
        self.update_persistence_button()

    def share_mode_clicked(self):
        self.common.log("Tab", "share_mode_clicked")
        self.mode = self.common.gui.MODE_SHARE
        self.new_tab.hide()

        self.share_mode = ShareMode(
            self.common,
            self.common.gui.qtapp,
            self.app,
            self.status_bar,
            self.status_bar.server_status_label,
            self.system_tray,
            self.filenames,
            self.common.gui.local_only,
        )
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
        self.share_mode.set_server_active.connect(self.set_server_active)

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_share_button"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def receive_mode_clicked(self):
        self.common.log("Tab", "receive_mode_clicked")
        self.mode = self.common.gui.MODE_RECEIVE
        self.new_tab.hide()

        self.receive_mode = ReceiveMode(
            self.common,
            self.common.gui.qtapp,
            self.app,
            self.status_bar,
            self.status_bar.server_status_label,
            self.system_tray,
            None,
            self.common.gui.local_only,
        )
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
        self.receive_mode.set_server_active.connect(self.set_server_active)

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_receive_button"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def website_mode_clicked(self):
        self.common.log("Tab", "website_mode_clicked")
        self.mode = self.common.gui.MODE_WEBSITE
        self.new_tab.hide()

        self.website_mode = WebsiteMode(
            self.common,
            self.common.gui.qtapp,
            self.app,
            self.status_bar,
            self.status_bar.server_status_label,
            self.system_tray,
            self.filenames,
        )
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
        self.website_mode.set_server_active.connect(self.set_server_active)

        self.change_title.emit(self.tab_id, strings._("gui_new_tab_website_button"))

        self.update_server_status_indicator()
        self.timer.start(500)

    def update_server_status_indicator(self):
        # Set the status image
        if self.mode == self.common.gui.MODE_SHARE:
            # Share mode
            if self.share_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_stopped)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_share_stopped")
                )
            elif self.share_mode.server_status.status == ServerStatus.STATUS_WORKING:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_working)
                )
                if self.share_mode.server_status.autostart_timer_datetime:
                    self.status_bar.server_status_label.setText(
                        strings._("gui_status_indicator_share_scheduled")
                    )
                else:
                    self.status_bar.server_status_label.setText(
                        strings._("gui_status_indicator_share_working")
                    )
            elif self.share_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_started)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_share_started")
                )
        elif self.mode == self.common.gui.MODE_WEBSITE:
            # Website mode
            if self.website_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_stopped)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_share_stopped")
                )
            elif self.website_mode.server_status.status == ServerStatus.STATUS_WORKING:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_working)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_share_working")
                )
            elif self.website_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_started)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_share_started")
                )
        elif self.mode == self.common.gui.MODE_RECEIVE:
            # Receive mode
            if self.receive_mode.server_status.status == ServerStatus.STATUS_STOPPED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_stopped)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_receive_stopped")
                )
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_WORKING:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_working)
                )
                if self.receive_mode.server_status.autostart_timer_datetime:
                    self.status_bar.server_status_label.setText(
                        strings._("gui_status_indicator_receive_scheduled")
                    )
                else:
                    self.status_bar.server_status_label.setText(
                        strings._("gui_status_indicator_receive_working")
                    )
            elif self.receive_mode.server_status.status == ServerStatus.STATUS_STARTED:
                self.status_bar.server_status_image_label.setPixmap(
                    QtGui.QPixmap.fromImage(self.status_bar.server_status_image_started)
                )
                self.status_bar.server_status_label.setText(
                    strings._("gui_status_indicator_receive_started")
                )

    def stop_server_finished(self):
        # When the server stopped, cleanup the ephemeral onion service
        self.common.gui.onion.cleanup(stop_tor=False)

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

                self.share_mode.handle_tor_broke()
                self.receive_mode.handle_tor_broke()
                self.website_mode.handle_tor_broke()

        # Process events from the web object
        if self.mode == self.common.gui.MODE_SHARE:
            mode = self.share_mode
        elif self.mode == self.common.gui.MODE_WEBSITE:
            mode = self.website_mode
        else:
            mode = self.receive_mode

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

    def set_server_active(self, active):
        """
        Disable the Settings and Receive Files buttons while an Share Files server is active.
        """
        pass
        """
        if active:
            self.settings_button.hide()
            if self.mode == self.common.gui.MODE_SHARE:
                self.share_mode_button.show()
                self.receive_mode_button.hide()
                self.website_mode_button.hide()
            elif self.mode == self.common.gui.MODE_WEBSITE:
                self.share_mode_button.hide()
                self.receive_mode_button.hide()
                self.website_mode_button.show()
            else:
                self.share_mode_button.hide()
                self.receive_mode_button.show()
                self.website_mode_button.hide()
        else:
            self.settings_button.show()
            self.share_mode_button.show()
            self.receive_mode_button.show()
            self.website_mode_button.show()

        # Disable settings menu action when server is active
        self.settings_action.setEnabled(not active)
        """

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def persistence_button_clicked(self):
        self.common.log("Tab", "persistence_button_clicked")
        if self.tab_settings["persistence"]:
            self.tab_settings["persistence"] = False
        else:
            self.tab_settings["persistence"] = True
        self.update_persistence_button()

    def update_persistence_button(self):
        self.common.log("Tab", "update_persistence_button")
        if self.tab_settings["persistence"]:
            self.persistence_button.setIcon(
                QtGui.QIcon(
                    self.common.get_resource_path("images/persistent_enabled.png")
                )
            )
        else:
            self.persistence_button.setIcon(
                QtGui.QIcon(
                    self.common.get_resource_path("images/persistent_disabled.png")
                )
            )

    def close_tab(self):
        self.common.log("Tab", "close_tab")
        if self.mode is None:
            return True

        if self.mode == self.common.gui.MODE_SHARE:
            server_status = self.share_mode.server_status
        elif self.mode == self.common.gui.MODE_RECEIVE:
            server_status = self.receive_mode.server_status
        else:
            server_status = self.website_mode.server_status

        if server_status.status == server_status.STATUS_STOPPED:
            return True
        else:
            self.common.log("Tab", "close_tab, opening warning dialog")
            dialog = QtWidgets.QMessageBox()
            dialog.setWindowTitle(strings._("gui_close_tab_warning_title"))
            if self.mode == self.common.gui.MODE_SHARE:
                dialog.setText(strings._("gui_close_tab_warning_share_description"))
            elif self.mode == self.common.gui.MODE_RECEIVE:
                dialog.setText(strings._("gui_close_tab_warning_receive_description"))
            else:
                dialog.setText(strings._("gui_close_tab_warning_website_description"))
            dialog.setIcon(QtWidgets.QMessageBox.Critical)
            dialog.addButton(
                strings._("gui_close_tab_warning_close"), QtWidgets.QMessageBox.YesRole
            )
            cancel_button = dialog.addButton(
                strings._("gui_close_tab_warning_cancel"), QtWidgets.QMessageBox.NoRole
            )
            dialog.setDefaultButton(cancel_button)
            reply = dialog.exec_()

            # Close
            if reply == 0:
                self.common.log("Tab", "close_tab", "close, closing tab")

                if self.mode == self.common.gui.MODE_SHARE:
                    self.share_mode.stop_server()
                elif self.mode == self.common.gui.MODE_RECEIVE:
                    self.receive_mode.stop_server()
                else:
                    self.website_mode.stop_server()

                self.app.cleanup()
                return True
            # Cancel
            else:
                self.common.log("Tab", "close_tab", "cancel, keeping tab open")
                return False

    def cleanup(self):
        self.app.cleanup()
