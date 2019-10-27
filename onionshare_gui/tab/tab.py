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

    def __init__(self, common, system_tray, status_bar, filenames):
        super(Tab, self).__init__()
        self.common = common
        self.common.log("Tab", "__init__")

        self.system_tray = system_tray
        self.status_bar = status_bar

        self.mode = self.common.gui.MODE_SHARE

        # Start the OnionShare app
        self.app = OnionShare(common, self.common.gui.onion, self.common.gui.local_only)

        # Mode switcher, to switch between share files and receive files
        self.share_mode_button = QtWidgets.QPushButton(
            strings._("gui_mode_share_button")
        )
        self.share_mode_button.setFixedHeight(50)
        self.share_mode_button.clicked.connect(self.share_mode_clicked)
        self.receive_mode_button = QtWidgets.QPushButton(
            strings._("gui_mode_receive_button")
        )
        self.receive_mode_button.setFixedHeight(50)
        self.receive_mode_button.clicked.connect(self.receive_mode_clicked)
        self.website_mode_button = QtWidgets.QPushButton(
            strings._("gui_mode_website_button")
        )
        self.website_mode_button.setFixedHeight(50)
        self.website_mode_button.clicked.connect(self.website_mode_clicked)
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setDefault(False)
        self.settings_button.setFixedWidth(40)
        self.settings_button.setFixedHeight(50)
        self.settings_button.setIcon(
            QtGui.QIcon(self.common.get_resource_path("images/settings.png"))
        )
        # self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet(self.common.gui.css["settings_button"])
        mode_switcher_layout = QtWidgets.QHBoxLayout()
        mode_switcher_layout.setSpacing(0)
        mode_switcher_layout.addWidget(self.share_mode_button)
        mode_switcher_layout.addWidget(self.receive_mode_button)
        mode_switcher_layout.addWidget(self.website_mode_button)
        mode_switcher_layout.addWidget(self.settings_button)

        # Server status indicator icons
        self.status_bar.server_status_image_stopped = QtGui.QImage(
            self.common.get_resource_path("images/server_stopped.png")
        )
        self.status_bar.server_status_image_working = QtGui.QImage(
            self.common.get_resource_path("images/server_working.png")
        )
        self.status_bar.server_status_image_started = QtGui.QImage(
            self.common.get_resource_path("images/server_started.png")
        )

        # Share mode
        self.share_mode = ShareMode(
            self.common,
            self.common.gui.qtapp,
            self.app,
            self.status_bar,
            self.status_bar.server_status_label,
            self.system_tray,
            filenames,
            self.common.gui.local_only,
        )
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

        # Receive mode
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

        # Website mode
        self.website_mode = WebsiteMode(
            self.common,
            self.common.gui.qtapp,
            self.app,
            self.status_bar,
            self.status_bar.server_status_label,
            self.system_tray,
            filenames,
        )
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

        self.update_mode_switcher()
        self.update_server_status_indicator()

        # Layouts
        contents_layout = QtWidgets.QVBoxLayout()
        contents_layout.setContentsMargins(10, 0, 10, 0)
        contents_layout.addWidget(self.receive_mode)
        contents_layout.addWidget(self.share_mode)
        contents_layout.addWidget(self.website_mode)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(mode_switcher_layout)
        layout.addLayout(contents_layout)
        self.setLayout(layout)

        # The server isn't active yet
        self.set_server_active(False)

        # Create the timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_callback)

        # Start the timer
        self.timer.start(500)

    def update_mode_switcher(self):
        # Based on the current mode, switch the mode switcher button styles,
        # and show and hide widgets to switch modes
        if self.mode == self.common.gui.MODE_SHARE:
            self.share_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_selected_style"]
            )
            self.receive_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )
            self.website_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )

            self.receive_mode.hide()
            self.share_mode.show()
            self.website_mode.hide()
        elif self.mode == self.common.gui.MODE_WEBSITE:
            self.share_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )
            self.receive_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )
            self.website_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_selected_style"]
            )

            self.receive_mode.hide()
            self.share_mode.hide()
            self.website_mode.show()
        else:
            self.share_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )
            self.receive_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_selected_style"]
            )
            self.website_mode_button.setStyleSheet(
                self.common.gui.css["mode_switcher_unselected_style"]
            )

            self.share_mode.hide()
            self.receive_mode.show()
            self.website_mode.hide()

        self.update_server_status_indicator()

    def share_mode_clicked(self):
        if self.mode != self.common.gui.MODE_SHARE:
            self.common.log("Tab", "share_mode_clicked")
            self.mode = self.common.gui.MODE_SHARE
            self.update_mode_switcher()

    def receive_mode_clicked(self):
        if self.mode != self.common.gui.MODE_RECEIVE:
            self.common.log("Tab", "receive_mode_clicked")
            self.mode = self.common.gui.MODE_RECEIVE
            self.update_mode_switcher()

    def website_mode_clicked(self):
        if self.mode != self.common.gui.MODE_WEBSITE:
            self.common.log("Tab", "website_mode_clicked")
            self.mode = self.common.gui.MODE_WEBSITE
            self.update_mode_switcher()

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
        else:
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
        # self.settings_action.setEnabled(not active)

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def close_event(self, e):
        self.common.log("Tab", "close_event")
        try:
            if self.mode == self.common.gui.MODE_WEBSITE:
                server_status = self.share_mode.server_status
            if self.mode == self.common.gui.MODE_WEBSITE:
                server_status = self.website_mode.server_status
            else:
                server_status = self.receive_mode.server_status
            if server_status.status != server_status.STATUS_STOPPED:
                self.common.log("MainWindow", "closeEvent, opening warning dialog")
                dialog = QtWidgets.QMessageBox()
                dialog.setWindowTitle(strings._("gui_quit_title"))
                if self.mode == self.common.gui.MODE_WEBSITE:
                    dialog.setText(strings._("gui_share_quit_warning"))
                else:
                    dialog.setText(strings._("gui_receive_quit_warning"))
                dialog.setIcon(QtWidgets.QMessageBox.Critical)
                quit_button = dialog.addButton(
                    strings._("gui_quit_warning_quit"), QtWidgets.QMessageBox.YesRole
                )
                dont_quit_button = dialog.addButton(
                    strings._("gui_quit_warning_dont_quit"),
                    QtWidgets.QMessageBox.NoRole,
                )
                dialog.setDefaultButton(dont_quit_button)
                reply = dialog.exec_()

                # Quit
                if reply == 0:
                    self.stop_server()
                    e.accept()
                # Don't Quit
                else:
                    e.ignore()

        except:
            e.accept()

    def cleanup(self):
        self.app.cleanup()
