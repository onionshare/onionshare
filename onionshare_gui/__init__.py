# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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
from __future__ import division
import os, sys, subprocess, inspect, platform, argparse, threading, time, math, inspect
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot

import onionshare
from onionshare import strings, helpers, web
from onionshare.settings import Settings

from .menu import Menu
from .file_selection import FileSelection
from .server_status import ServerStatus
from .downloads import Downloads
from .alert import Alert
from .update_checker import UpdateThread

class Application(QtWidgets.QApplication):
    """
    This is Qt's QApplication class. It has been overridden to support threads
    and the quick keyboard shortcut.
    """
    def __init__(self):
        system = platform.system()
        if system == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.key() == QtCore.Qt.Key_Q and
            event.modifiers() == QtCore.Qt.ControlModifier):
                self.quit()
        return False


class OnionShareGui(QtWidgets.QMainWindow):
    """
    OnionShareGui is the main window for the GUI that contains all of the
    GUI elements.
    """
    start_server_finished = QtCore.pyqtSignal()
    stop_server_finished = QtCore.pyqtSignal()
    starting_server_step2 = QtCore.pyqtSignal()
    starting_server_step3 = QtCore.pyqtSignal()
    starting_server_error = QtCore.pyqtSignal(str)

    def __init__(self, qtapp, app):
        super(OnionShareGui, self).__init__()
        self.qtapp = qtapp
        self.app = app

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(QtGui.QIcon(helpers.get_resource_path('images/logo.png')))

        # Menu bar
        self.setMenuBar(Menu(self.qtapp))

        # Check for updates in a new thread, if enabled
        system = platform.system()
        if system == 'Windows' or system == 'Darwin':
            settings = Settings()
            settings.load()
            if settings.get('use_autoupdate'):
                # TODO: make updates actually work
                print("Updating in another thread")
                #t = UpdateThread()
                #t.start()

    def send_files(self, filenames=None):
        """
        Build the GUI in send files mode.
        Note that this is the only mode currently implemented.
        """
        # file selection
        self.file_selection = FileSelection()
        if filenames:
            for filename in filenames:
                self.file_selection.file_list.add_file(filename)

        # server status
        self.server_status = ServerStatus(self.qtapp, self.app, web, self.file_selection)
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.stop_server)
        self.start_server_finished.connect(self.clear_message)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
        self.server_status.url_copied.connect(self.copy_url)
        self.server_status.hidservauth_copied.connect(self.copy_hidservauth)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)

        # filesize warning
        self.filesize_warning = QtWidgets.QLabel()
        self.filesize_warning.setStyleSheet('padding: 10px 0; font-weight: bold; color: #333333;')
        self.filesize_warning.hide()

        # downloads
        self.downloads = Downloads()
        self.downloads_container = QtWidgets.QScrollArea()
        self.downloads_container.setWidget(self.downloads)
        self.downloads_container.setWidgetResizable(True)
        self.downloads_container.setMaximumHeight(200)
        self.vbar = self.downloads_container.verticalScrollBar()
        self.downloads_container.hide() # downloads start out hidden
        self.new_download = False

        # status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        version_label = QtWidgets.QLabel('v{0:s}'.format(helpers.get_version()))
        version_label.setStyleSheet('color: #666666; padding: 0 10px;')
        self.status_bar.addPermanentWidget(version_label)
        self.setStatusBar(self.status_bar)

        # status bar, zip progress bar
        self._zip_progress_bar = None

        # main layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.file_selection)
        self.layout.addLayout(self.server_status)
        self.layout.addWidget(self.filesize_warning)
        self.layout.addWidget(self.downloads_container)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.show()

        # check for requests frequently
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_for_requests)
        self.timer.start(500)

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        # First, load settings and configure
        settings = Settings()
        settings.load()
        self.app.set_stealth(settings.get('use_stealth'))
        web.set_stay_open(not settings.get('close_after_first_download'))

        # Reset web counters
        web.download_count = 0
        web.error404_count = 0
        web.set_gui_mode()

        # pick an available local port for the http service to listen on
        self.app.choose_port()

        # start onionshare http service in new thread
        t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open, self.app.transparent_torification))
        t.daemon = True
        t.start()
        # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
        time.sleep(0.2)

        # start the onion service in a new thread
        def start_onion_service(self):
            try:
                # Show Tor connection status if connection type is bundled tor
                if settings.get('connection_type') == 'bundled':
                    def bundled_tor_func(message):
                        self.status_bar.showMessage(message)
                        if 'Done' in message:
                            self.status_bar.showMessage(strings._('gui_starting_server1', True))
                else:
                    self.status_bar.showMessage(strings._('gui_starting_server1', True))
                    bundled_tor_func = None

                self.app.start_onion_service(bundled_tor_func)
                self.starting_server_step2.emit()

            except (onionshare.onion.TorTooOld, onionshare.onion.TorErrorInvalidSetting, onionshare.onion.TorErrorAutomatic, onionshare.onion.TorErrorSocketPort, onionshare.onion.TorErrorSocketFile, onionshare.onion.TorErrorMissingPassword, onionshare.onion.TorErrorUnreadableCookieFile, onionshare.onion.TorErrorAuthError, onionshare.onion.TorErrorProtocolError, onionshare.onion.BundledTorTimeout) as e:
                self.starting_server_error.emit(e.args[0])
                return

        t = threading.Thread(target=start_onion_service, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server. Zipping up files.
        """
        # add progress bar to the status bar, indicating the crunching of files.
        self._zip_progress_bar = ZipProgressBar(0)
        self._zip_progress_bar.total_files_size = OnionShareGui._compute_total_size(
            self.file_selection.file_list.filenames)
        self.status_bar.clearMessage()
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            def _set_processed_size(x):
                if self._zip_progress_bar != None:
                    self._zip_progress_bar.update_processed_size_signal.emit(x)
            web.set_file_info(self.file_selection.file_list.filenames, processed_size_callback=_set_processed_size)
            self.app.cleanup_filenames.append(web.zip_filename)
            self.starting_server_step3.emit()

            # done
            self.start_server_finished.emit()

        #self.status_bar.showMessage(strings._('gui_starting_server2', True))
        t = threading.Thread(target=finish_starting_server, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step3(self):
        """
        Step 3 in starting the onionshare server. This displays the large filesize
        warning, if applicable.
        """
        # Remove zip progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        # warn about sending large files over Tor
        if web.zip_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        Alert(error, QtWidgets.QMessageBox.Warning)
        self.server_status.stop_server()
        self.status_bar.clearMessage()

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        if self.server_status.status != self.server_status.STATUS_STOPPED:
            web.stop(self.app.port)
        self.app.cleanup()
        self.filesize_warning.hide()
        self.stop_server_finished.emit()

    @staticmethod
    def _compute_total_size(filenames):
        total_size = 0
        for filename in filenames:
            if os.path.isfile(filename):
                total_size += os.path.getsize(filename)
            if os.path.isdir(filename):
                total_size += helpers.dir_size(filename)
        return total_size

    def check_for_requests(self):
        """
        Check for messages communicated from the web app, and update the GUI accordingly.
        """
        self.update()
        # scroll to the bottom of the dl progress bar log pane
        # if a new download has been added
        if self.new_download:
            self.vbar.setValue(self.vbar.maximum())
            self.new_download = False
        # only check for requests if the server is running
        if self.server_status.status != self.server_status.STATUS_STARTED:
            return

        events = []

        done = False
        while not done:
            try:
                r = web.q.get(False)
                events.append(r)
            except web.queue.Empty:
                done = True

        for event in events:
            if event["type"] == web.REQUEST_LOAD:
                self.status_bar.showMessage(strings._('download_page_loaded', True))

            elif event["type"] == web.REQUEST_DOWNLOAD:
                self.downloads_container.show() # show the downloads layout
                self.downloads.add_download(event["data"]["id"], web.zip_filesize)
                self.new_download = True

            elif event["type"] == web.REQUEST_RATE_LIMIT:
                self.stop_server()
                Alert(strings._('error_rate_limit'), QtWidgets.QMessageBox.Critical)

            elif event["type"] == web.REQUEST_PROGRESS:
                self.downloads.update_download(event["data"]["id"], event["data"]["bytes"])

                # is the download complete?
                if event["data"]["bytes"] == web.zip_filesize:
                    # close on finish?
                    if not web.get_stay_open():
                        self.server_status.stop_server()

            elif event["type"] == web.REQUEST_CANCELED:
                self.downloads.cancel_download(event["data"]["id"])

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('[#{0:d}] {1:s}: {2:s}'.format(web.error404_count, strings._('other_page_loaded', True), event["path"]))

    def copy_url(self):
        """
        When the URL gets copied to the clipboard, display this in the status bar.
        """
        self.status_bar.showMessage(strings._('gui_copied_url', True), 2000)

    def copy_hidservauth(self):
        """
        When the stealth onion service HidServAuth gets copied to the clipboard, display this in the status bar.
        """
        self.status_bar.showMessage(strings._('gui_copied_hidservauth', True), 2000)

    def clear_message(self):
        """
        Clear messages from the status bar.
        """
        self.status_bar.clearMessage()

    def closeEvent(self, e):
        if self.server_status.status != self.server_status.STATUS_STOPPED:
            dialog = QtWidgets.QMessageBox()
            dialog.setWindowTitle("OnionShare")
            dialog.setText(strings._('gui_quit_warning', True))
            quit_button = dialog.addButton(strings._('gui_quit_warning_quit', True), QtWidgets.QMessageBox.YesRole)
            dont_quit_button = dialog.addButton(strings._('gui_quit_warning_dont_quit', True), QtWidgets.QMessageBox.NoRole)
            dialog.setDefaultButton(dont_quit_button)
            reply = dialog.exec_()

            # Quit
            if reply == 0:
                self.stop_server()
                e.accept()
            # Don't Quit
            else:
                e.ignore()


class ZipProgressBar(QtWidgets.QProgressBar):
    update_processed_size_signal = QtCore.pyqtSignal(int)

    def __init__(self, total_files_size):
        super(ZipProgressBar, self).__init__()
        self.setMaximumHeight(15)
        self.setMinimumWidth(200)
        self.setValue(0)
        self.setFormat(strings._('zip_progress_bar_format'))
        self.setStyleSheet(
            "QProgressBar::chunk { background-color: #05B8CC; } "
        )

        self._total_files_size = total_files_size
        self._processed_size = 0

        self.update_processed_size_signal.connect(self.update_processed_size)

    @property
    def total_files_size(self):
        return self._total_files_size

    @total_files_size.setter
    def total_files_size(self, val):
        self._total_files_size = val

    @property
    def processed_size(self):
        return self._processed_size

    @processed_size.setter
    def processed_size(self, val):
        self.update_processed_size(val)

    def update_processed_size(self, val):
        self._processed_size = val
        if self.processed_size < self.total_files_size:
            self.setValue(int((self.processed_size * 100) / self.total_files_size))
        elif self.total_files_size != 0:
            self.setValue(100)
        else:
            self.setValue(0)


def main():
    """
    The main() function implements all of the logic that the GUI version of onionshare uses.
    """
    strings.load_strings(helpers)
    print(strings._('version_string').format(helpers.get_version()))

    # start the Qt app
    global qtapp
    qtapp = Application()

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('--transparent', action='store_true', dest='transparent_torification', help=strings._("help_transparent_torification"))
    parser.add_argument('--filenames', metavar='filenames', nargs='+', help=strings._('help_filename'))
    args = parser.parse_args()

    filenames = args.filenames
    if filenames:
        for i in range(len(filenames)):
            filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    stay_open = bool(args.stay_open)
    debug = bool(args.debug)
    transparent_torification = bool(args.transparent_torification)

    # validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.exists(filename):
                Alert(strings._("not_a_file", True).format(filename))
                valid = False
        if not valid:
            sys.exit()

    # start the onionshare app
    web.set_stay_open(stay_open)
    web.set_transparent_torification(transparent_torification)
    app = onionshare.OnionShare(debug, local_only, stay_open, transparent_torification)

    # clean up when app quits
    def shutdown():
        app.cleanup()
    qtapp.aboutToQuit.connect(shutdown)

    # launch the gui
    gui = OnionShareGui(qtapp, app)
    gui.send_files(filenames)

    # all done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
