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

from PySide2 import QtCore, QtWidgets

from onionshare_cli.common import AutoStopTimer

from .history import IndividualFileHistoryItem
from .mode_settings_widget import ModeSettingsWidget

from ..server_status import ServerStatus
from ... import strings
from ...threads import OnionThread, AutoStartTimer
from ...widgets import Alert, MinimumSizeWidget


class Mode(QtWidgets.QWidget):
    """
    The class that all modes inherit from
    """

    start_server_finished = QtCore.Signal()
    stop_server_finished = QtCore.Signal()
    starting_server_step2 = QtCore.Signal()
    starting_server_step3 = QtCore.Signal()
    starting_server_error = QtCore.Signal(str)
    starting_server_early = QtCore.Signal()
    set_server_active = QtCore.Signal(bool)
    change_persistent = QtCore.Signal(int, bool)

    def __init__(self, tab):
        super(Mode, self).__init__()
        self.tab = tab
        self.settings = tab.settings

        self.common = tab.common
        self.qtapp = self.common.gui.qtapp
        self.app = tab.app

        self.status_bar = tab.status_bar
        self.server_status_label = tab.status_bar.server_status_label
        self.system_tray = tab.system_tray

        self.filenames = tab.filenames

        # The web object gets created in init()
        self.web = None

        # Threads start out as None
        self.onion_thread = None
        self.web_thread = None
        self.startup_thread = None

        # Mode settings widget
        self.mode_settings_widget = ModeSettingsWidget(
            self.common, self.tab, self.settings
        )
        self.mode_settings_widget.change_persistent.connect(self.change_persistent)

        # Server status
        self.server_status = ServerStatus(
            self.common,
            self.qtapp,
            self.app,
            self.settings,
            self.mode_settings_widget,
            None,
            self.common.gui.local_only,
        )
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.stop_server)
        self.server_status.server_canceled.connect(self.cancel_server)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_early.connect(self.start_server_early)
        self.starting_server_error.connect(self.start_server_error)

        # Primary action
        # Note: It's up to the downstream Mode to add this to its layout
        self.primary_action_layout = QtWidgets.QVBoxLayout()
        self.primary_action_layout.addWidget(self.mode_settings_widget)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(self.primary_action_layout)

        # It's up to the downstream Mode to add stuff to self.content_layout
        # self.content_layout shows the actual content of the mode
        # self.tor_not_connected_layout is displayed when Tor isn't connected
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_widget = QtWidgets.QWidget()
        self.content_widget.setLayout(self.content_layout)

        tor_not_connected_label = QtWidgets.QLabel(
            strings._("mode_tor_not_connected_label")
        )
        tor_not_connected_label.setAlignment(QtCore.Qt.AlignHCenter)
        tor_not_connected_label.setStyleSheet(
            self.common.gui.css["tor_not_connected_label"]
        )
        self.tor_not_connected_layout = QtWidgets.QVBoxLayout()
        self.tor_not_connected_layout.addStretch()
        self.tor_not_connected_layout.addWidget(tor_not_connected_label)
        self.tor_not_connected_layout.addWidget(MinimumSizeWidget(700, 0))
        self.tor_not_connected_layout.addStretch()
        self.tor_not_connected_widget = QtWidgets.QWidget()
        self.tor_not_connected_widget.setLayout(self.tor_not_connected_layout)

        self.wrapper_layout = QtWidgets.QVBoxLayout()
        self.wrapper_layout.addWidget(self.content_widget)
        self.wrapper_layout.addWidget(self.tor_not_connected_widget)
        self.setLayout(self.wrapper_layout)

        if self.common.gui.onion.connected_to_tor:
            self.tor_connection_started()
        else:
            self.tor_connection_stopped()

    def init(self):
        """
        Add custom initialization here.
        """
        pass

    def get_type(self):
        """
        Returns the type of mode as a string (e.g. "share", "receive", etc.)
        """
        pass

    def human_friendly_time(self, secs):
        """
        Returns a human-friendly time delta from given seconds.
        """
        days = secs // 86400
        hours = (secs - days * 86400) // 3600
        minutes = (secs - days * 86400 - hours * 3600) // 60
        seconds = secs - days * 86400 - hours * 3600 - minutes * 60
        if not seconds:
            seconds = "0"
        result = (
            (f"{days}{strings._('days_first_letter')}, " if days else "")
            + (f"{hours}{strings._('hours_first_letter')}, " if hours else "")
            + (f"{minutes}{strings._('minutes_first_letter')}, " if minutes else "")
            + f"{seconds}{strings._('seconds_first_letter')}"
        )

        return result

    def timer_callback(self):
        """
        This method is called regularly on a timer.
        """
        # If this is a scheduled share, display the countdown til the share starts
        if self.server_status.status == ServerStatus.STATUS_WORKING:
            if self.settings.get("general", "autostart_timer"):
                now = QtCore.QDateTime.currentDateTime()
                if self.server_status.local_only:
                    seconds_remaining = now.secsTo(
                        self.mode_settings_widget.autostart_timer_widget.dateTime()
                    )
                else:
                    seconds_remaining = now.secsTo(
                        self.server_status.autostart_timer_datetime.replace(
                            second=0, microsecond=0
                        )
                    )
                # Update the server button
                if seconds_remaining > 0:
                    self.server_status.server_button.setText(
                        strings._("gui_waiting_to_start").format(
                            self.human_friendly_time(seconds_remaining)
                        )
                    )
                else:
                    if self.common.platform == "Windows" or self.settings.get(
                        "general", "autostart_timer"
                    ):
                        self.server_status.server_button.setText(
                            strings._("gui_please_wait")
                        )
                    else:
                        self.server_status.server_button.setText(
                            strings._("gui_please_wait_no_button")
                        )

        # If the auto-stop timer has stopped, stop the server
        if self.server_status.status == ServerStatus.STATUS_STARTED:
            if self.app.autostop_timer_thread and self.settings.get(
                "general", "autostop_timer"
            ):
                if self.autostop_timer_datetime_delta > 0:
                    now = QtCore.QDateTime.currentDateTime()
                    seconds_remaining = now.secsTo(
                        self.server_status.autostop_timer_datetime
                    )

                    # Update the server button
                    server_button_text = self.get_stop_server_autostop_timer_text()
                    self.server_status.server_button.setText(
                        server_button_text.format(
                            self.human_friendly_time(seconds_remaining)
                        )
                    )

                    self.status_bar.clearMessage()
                    if not self.app.autostop_timer_thread.is_alive():
                        self.autostop_timer_finished_should_stop_server()

    def timer_callback_custom(self):
        """
        Add custom timer code.
        """
        pass

    def get_stop_server_autostop_timer_text(self):
        """
        Return the string to put on the stop server button, if there's an auto-stop timer
        """
        pass

    def autostop_timer_finished_should_stop_server(self):
        """
        The auto-stop timer expired, should we stop the server? Returns a bool
        """
        pass

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        self.common.log("Mode", "start_server")

        self.start_server_custom()
        self.set_server_active.emit(True)

        # Clear the status bar
        self.status_bar.clearMessage()
        self.server_status_label.setText("")

        # Hide the mode settings
        self.mode_settings_widget.hide()

        # Ensure we always get a new random port each time we might launch an OnionThread
        self.app.port = None

        # Start the onion thread. If this share was scheduled for a future date,
        # the OnionThread will start and exit 'early' to obtain the port, password
        # and onion address, but it will not start the WebThread yet.
        if self.settings.get("general", "autostart_timer"):
            self.start_onion_thread(obtain_onion_early=True)
            self.common.log("Mode", "start_server", "Starting auto-start timer")
            self.startup_thread = AutoStartTimer(self)
            # Once the timer has finished, start the real share, with a WebThread
            self.startup_thread.success.connect(self.start_scheduled_service)
            self.startup_thread.error.connect(self.start_server_error)
            self.startup_thread.canceled = False
            self.startup_thread.start()
        else:
            self.start_onion_thread()

    def start_onion_thread(self, obtain_onion_early=False):
        # If we tried to start with Client Auth and our Tor is too old to support it,
        # bail out early
        if (
            not self.server_status.local_only
            and not self.app.onion.supports_stealth
            and not self.settings.get("general", "public")
        ):
            self.stop_server()
            self.start_server_error(strings._("gui_server_doesnt_support_stealth"))
        else:
            self.common.log("Mode", "start_server", "Starting an onion thread")
            self.obtain_onion_early = obtain_onion_early
            self.onion_thread = OnionThread(self)
            self.onion_thread.success.connect(self.starting_server_step2.emit)
            self.onion_thread.success_early.connect(self.starting_server_early.emit)
            self.onion_thread.error.connect(self.starting_server_error.emit)
            self.onion_thread.start()

    def start_scheduled_service(self, obtain_onion_early=False):
        # We start a new OnionThread with the saved scheduled key from settings
        self.common.settings.load()
        self.obtain_onion_early = obtain_onion_early
        self.common.log("Mode", "start_server", "Starting a scheduled onion thread")
        self.onion_thread = OnionThread(self)
        self.onion_thread.success.connect(self.starting_server_step2.emit)
        self.onion_thread.error.connect(self.starting_server_error.emit)
        self.onion_thread.start()

    def start_server_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def start_server_early(self):
        """
        An 'early' start of an onion service in order to obtain the onion
        address for a scheduled start. Shows the onion address in the UI
        in advance of actually starting the share.
        """
        self.server_status.show_url()

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server.
        """
        self.common.log("Mode", "start_server_step2")

        self.start_server_step2_custom()

        # Nothing to do here.

        # start_server_step2_custom has call these to move on:
        # self.starting_server_step3.emit()
        # self.start_server_finished.emit()

    def start_server_step2_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def start_server_step3(self):
        """
        Step 3 in starting the onionshare server.
        """
        self.common.log("Mode", "start_server_step3")

        self.start_server_step3_custom()

        if self.settings.get("general", "autostop_timer"):
            # Convert the date value to seconds between now and then
            now = QtCore.QDateTime.currentDateTime()
            self.autostop_timer_datetime_delta = now.secsTo(
                self.server_status.autostop_timer_datetime
            )
            # Start the auto-stop timer
            if self.autostop_timer_datetime_delta > 0:
                self.app.autostop_timer_thread = AutoStopTimer(
                    self.common, self.autostop_timer_datetime_delta
                )
                self.app.autostop_timer_thread.start()
            # The auto-stop timer has actually already passed since the user clicked Start. Probably the Onion service took too long to start.
            else:
                self.stop_server()
                self.start_server_error(
                    strings._("gui_server_started_after_autostop_timer")
                )

    def start_server_step3_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        self.common.log("Mode", "start_server_error")

        Alert(self.common, error, QtWidgets.QMessageBox.Warning)
        self.set_server_active.emit(False)
        self.server_status.stop_server()
        self.status_bar.clearMessage()

        self.start_server_error_custom()

    def start_server_error_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def cancel_server(self):
        """
        Cancel the server while it is preparing to start
        """
        self.cancel_server_custom()
        if self.startup_thread:
            self.common.log("Mode", "cancel_server: quitting startup thread")
            self.startup_thread.canceled = True
            self.app.onion.scheduled_key = None
            self.app.onion.scheduled_auth_cookie = None
            self.startup_thread.quit()

        # Canceling only works in Windows
        # https://github.com/onionshare/onionshare/issues/1371
        if self.common.platform == "Windows":
            if self.onion_thread:
                self.common.log("Mode", "cancel_server: quitting onion thread")
                self.onion_thread.terminate()
                self.onion_thread.wait()
            if self.web_thread:
                self.common.log("Mode", "cancel_server: quitting web thread")
                self.web_thread.terminate()
                self.web_thread.wait()

        self.stop_server()

    def cancel_server_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        self.common.log("Mode", "stop_server")

        if self.server_status.status != ServerStatus.STATUS_STOPPED:
            try:
                self.web.stop(self.app.port)
            except Exception:
                # Probably we had no port to begin with (Onion service didn't start)
                pass
        self.web.cleanup()

        self.stop_server_custom()

        self.set_server_active.emit(False)
        self.stop_server_finished.emit()

        # Show the mode settings
        self.mode_settings_widget.show()

    def stop_server_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def handle_tor_broke(self):
        """
        Handle connection from Tor breaking.
        """
        if self.server_status.status != ServerStatus.STATUS_STOPPED:
            self.server_status.stop_server()
        self.handle_tor_broke_custom()

    def handle_tor_broke_custom(self):
        """
        Add custom initialization here.
        """
        pass

    # Handle web server events

    def handle_request_load(self, event):
        """
        Handle REQUEST_LOAD event.
        """
        pass

    def handle_request_started(self, event):
        """
        Handle REQUEST_STARTED event.
        """
        pass

    def handle_request_progress(self, event):
        """
        Handle REQUEST_PROGRESS event.
        """
        pass

    def handle_request_canceled(self, event):
        """
        Handle REQUEST_CANCELED event.
        """
        pass

    def handle_request_upload_includes_message(self, event):
        """
        Handle REQUEST_UPLOAD_INCLUDES_MESSAGE event.
        """
        pass

    def handle_request_upload_file_renamed(self, event):
        """
        Handle REQUEST_UPLOAD_FILE_RENAMED event.
        """
        pass

    def handle_request_upload_message(self, event):
        """
        Handle REQUEST_UPLOAD_MESSAGE event.
        """
        pass

    def handle_request_upload_set_dir(self, event):
        """
        Handle REQUEST_UPLOAD_SET_DIR event.
        """
        pass

    def handle_request_upload_finished(self, event):
        """
        Handle REQUEST_UPLOAD_FINISHED event.
        """
        pass

    def handle_request_upload_canceled(self, event):
        """
        Handle REQUEST_UPLOAD_CANCELED event.
        """
        pass

    def handle_request_individual_file_started(self, event):
        """
        Handle REQUEST_INDVIDIDUAL_FILES_STARTED event.
        Used in both Share and Website modes, so implemented here.
        """
        self.toggle_history.update_indicator(True)
        self.history.requests_count += 1
        self.history.update_requests()

        item = IndividualFileHistoryItem(self.common, event["data"], event["path"])
        self.history.add(event["data"]["id"], item)

    def handle_request_individual_file_progress(self, event):
        """
        Handle REQUEST_INDVIDIDUAL_FILES_PROGRESS event.
        Used in both Share and Website modes, so implemented here.
        """
        self.history.update(event["data"]["id"], event["data"]["bytes"])

        if self.server_status.status == self.server_status.STATUS_STOPPED:
            self.history.cancel(event["data"]["id"])

    def handle_request_individual_file_canceled(self, event):
        """
        Handle REQUEST_INDVIDIDUAL_FILES_CANCELED event.
        Used in both Share and Website modes, so implemented here.
        """
        self.history.cancel(event["data"]["id"])

    def tor_connection_started(self):
        """
        This is called on every Mode when Tor is connected
        """
        self.content_widget.show()
        self.tor_not_connected_widget.hide()

    def tor_connection_stopped(self):
        """
        This is called on every Mode when Tor is disconnected
        """
        if self.common.gui.local_only:
            self.tor_connection_started()
            return

        self.content_widget.hide()
        self.tor_not_connected_widget.show()
