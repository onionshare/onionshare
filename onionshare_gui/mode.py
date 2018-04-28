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
import time
import threading
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from onionshare.common import ShutdownTimer

from .server_status import ServerStatus
from .onion_thread import OnionThread
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

    def __init__(self, common, qtapp, app, status_bar, server_status_label, system_tray, filenames=None):
        super(Mode, self).__init__()
        self.common = common
        self.qtapp = qtapp
        self.app = app

        self.status_bar = status_bar
        self.server_status_label = server_status_label
        self.system_tray = system_tray

        self.filenames = filenames

        # The web object gets created in init()
        self.web = None

        # Server status
        self.server_status = ServerStatus(self.common, self.qtapp, self.app)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.stop_server)
        self.server_status.server_canceled.connect(self.cancel_server)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)

        # Primary action layout
        self.primary_action_layout = QtWidgets.QVBoxLayout()
        self.primary_action_layout.addWidget(self.server_status)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(self.primary_action_layout)

        # Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.primary_action)
        self.setLayout(self.layout)

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

        # Start the onion service in a new thread
        def start_onion_service(self):
            # Choose a port for the web app
            self.app.choose_port()

            # Start http service in new thread
            t = threading.Thread(target=self.web.start, args=(self.app.port, self.app.stay_open, self.common.settings.get('slug')))
            t.daemon = True
            t.start()

            # Wait for the web app slug to generate before continuing
            while self.web.slug == None:
                time.sleep(0.1)

            # Now start the onion service
            try:
                self.app.start_onion_service()
                self.starting_server_step2.emit()

            except Exception as e:
                self.starting_server_error.emit(e.args[0])
                return

            self.app.stay_open = not self.common.settings.get('close_after_first_download')

        self.common.log('Mode', 'start_server', 'Starting an onion thread')
        self.t = OnionThread(self.common, function=start_onion_service, kwargs={'self': self})
        self.t.daemon = True
        self.t.start()
    
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
        if self.t:
            self.t.quit()
        self.stop_server()

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
