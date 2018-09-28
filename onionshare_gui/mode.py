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
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.common import ShutdownTimer

from .server_status import ServerStatus
from .threads import OnionThread
from .widgets import Alert

class Mode(QtWidgets.QWidget):
    """
    The class that ShareMode and ReceiveMode inherit from.
    """
    start_server_finished = QtCore.pyqtSignal()
    stop_server_finished = QtCore.pyqtSignal()
    starting_server_step2 = QtCore.pyqtSignal()
    starting_server_step3 = QtCore.pyqtSignal()
    starting_server_error = QtCore.pyqtSignal(str)
    set_server_active = QtCore.pyqtSignal(bool)
    adjust_size = QtCore.pyqtSignal(int)

    def __init__(self, common, qtapp, app, status_bar, server_status_label, system_tray, filenames=None, local_only=False):
        super(Mode, self).__init__()
        self.common = common
        self.qtapp = qtapp
        self.app = app

        self.status_bar = status_bar
        self.server_status_label = server_status_label
        self.system_tray = system_tray

        self.filenames = filenames

        self.setMinimumWidth(450)

        # The web object gets created in init()
        self.web = None

        # Local mode is passed from OnionShareGui
        self.local_only = local_only

        # Threads start out as None
        self.onion_thread = None
        self.web_thread = None

        # Server status
        self.server_status = ServerStatus(self.common, self.qtapp, self.app, None, self.local_only)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.stop_server)
        self.server_status.server_canceled.connect(self.cancel_server)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)

        # Primary action
        # Note: It's up to the downstream Mode to add this to its layout
        self.primary_action_layout = QtWidgets.QVBoxLayout()
        self.primary_action_layout.addWidget(self.server_status)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(self.primary_action_layout)

        # Hack to allow a minimum width on the main layout
        # Note: It's up to the downstream Mode to add this to its layout
        self.min_width_widget = QtWidgets.QWidget()
        self.min_width_widget.setMinimumWidth(450)

    def init(self):
        """
        Add custom initialization here.
        """
        pass

    def timer_callback(self):
        """
        This method is called regularly on a timer.
        """
        # If the auto-shutdown timer has stopped, stop the server
        if self.server_status.status == ServerStatus.STATUS_STARTED:
            if self.app.shutdown_timer and self.common.settings.get('shutdown_timeout'):
                if self.timeout > 0:
                    now = QtCore.QDateTime.currentDateTime()
                    seconds_remaining = now.secsTo(self.server_status.timeout)

                    # Update the server button
                    server_button_text = self.get_stop_server_shutdown_timeout_text()
                    self.server_status.server_button.setText(server_button_text.format(seconds_remaining))

                    self.status_bar.clearMessage()
                    if not self.app.shutdown_timer.is_alive():
                        if self.timeout_finished_should_stop_server():
                            self.server_status.stop_server()

    def timer_callback_custom(self):
        """
        Add custom timer code.
        """
        pass

    def get_stop_server_shutdown_timeout_text(self):
        """
        Return the string to put on the stop server button, if there's a shutdown timeout
        """
        pass

    def timeout_finished_should_stop_server(self):
        """
        The shutdown timer expired, should we stop the server? Returns a bool
        """
        pass

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        self.common.log('Mode', 'start_server')

        self.start_server_custom()

        self.set_server_active.emit(True)
        self.app.set_stealth(self.common.settings.get('use_stealth'))

        # Clear the status bar
        self.status_bar.clearMessage()
        self.server_status_label.setText('')

        self.common.log('Mode', 'start_server', 'Starting an onion thread')
        self.onion_thread = OnionThread(self)
        self.onion_thread.success.connect(self.starting_server_step2.emit)
        self.onion_thread.error.connect(self.starting_server_error.emit)
        self.onion_thread.start()

    def start_server_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server.
        """
        self.common.log('Mode', 'start_server_step2')

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
        self.common.log('Mode', 'start_server_step3')

        self.start_server_step3_custom()

        if self.common.settings.get('shutdown_timeout'):
            # Convert the date value to seconds between now and then
            now = QtCore.QDateTime.currentDateTime()
            self.timeout = now.secsTo(self.server_status.timeout)
            # Set the shutdown timeout value
            if self.timeout > 0:
                self.app.shutdown_timer = ShutdownTimer(self.common, self.timeout)
                self.app.shutdown_timer.start()
            # The timeout has actually already passed since the user clicked Start. Probably the Onion service took too long to start.
            else:
                self.stop_server()
                self.start_server_error(strings._('gui_server_started_after_timeout'))

    def start_server_step3_custom(self):
        """
        Add custom initialization here.
        """
        pass

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        self.common.log('Mode', 'start_server_error')

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

        if self.onion_thread:
            self.common.log('Mode', 'cancel_server: quitting onion thread')
            self.onion_thread.quit()
        if self.web_thread:
            self.common.log('Mode', 'cancel_server: quitting web thread')
            self.web_thread.quit()
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
        self.common.log('Mode', 'stop_server')

        if self.server_status.status != ServerStatus.STATUS_STOPPED:
            try:
                self.web.stop(self.app.port)
            except:
                # Probably we had no port to begin with (Onion service didn't start)
                pass
        self.app.cleanup()

        self.stop_server_custom()

        self.set_server_active.emit(False)
        self.stop_server_finished.emit()

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

    def handle_request_rate_limit(self, event):
        """
        Handle REQUEST_RATE_LIMIT event.
        """
        self.stop_server()
        Alert(self.common, strings._('error_rate_limit'), QtWidgets.QMessageBox.Critical)

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

    def handle_request_close_server(self, event):
        """
        Handle REQUEST_CLOSE_SERVER event.
        """
        pass

    def handle_request_upload_file_renamed(self, event):
        """
        Handle REQUEST_UPLOAD_FILE_RENAMED event.
        """
        pass

    def handle_request_upload_finished(self, event):
        """
        Handle REQUEST_UPLOAD_FINISHED event.
        """
        pass

    def resize_window(self):
        """
        We call this to force the OnionShare window to resize itself to be smaller.
        For this to do anything, the Mode needs to override it and call:

        self.adjust_size.emit(min_width)

        It can calculate min_width (the new minimum window width) based on what
        widgets are visible.
        """
        pass

    def show(self):
        """
        Always resize the window after showing this Mode widget.
        """
        super(Mode, self).show()
        self.qtapp.processEvents()
        self.resize_window()
