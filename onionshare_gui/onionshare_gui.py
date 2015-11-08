# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
import os, sys, subprocess, inspect, platform, argparse, threading, time, math, inspect, platform
from PyQt4 import QtCore, QtGui

import common

try:
    import onionshare
except ImportError:
    sys.path.append(os.path.abspath(common.onionshare_gui_dir + "/.."))
    import onionshare
from onionshare import strings, helpers, web

from file_selection import FileSelection
from server_status import ServerStatus
from downloads import Downloads
from options import Options


class Application(QtGui.QApplication):
    def __init__(self):
        platform = helpers.get_platform()
        if platform == 'Tails' or platform == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtGui.QApplication.__init__(self, sys.argv)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.key() == QtCore.Qt.Key_Q and
            event.modifiers() == QtCore.Qt.ControlModifier):
                self.quit()
        return False


class OnionShareGui(QtGui.QWidget):
    start_server_finished = QtCore.pyqtSignal()
    stop_server_finished = QtCore.pyqtSignal()
    starting_server_step2 = QtCore.pyqtSignal()

    def __init__(self, qtapp, app):
        super(OnionShareGui, self).__init__()
        self.qtapp = qtapp
        self.app = app

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(window_icon)

    def send_files(self, filenames=None):
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
        self.starting_server_step2.connect(self.start_server_step2)

        # filesize warning
        self.filesize_warning = QtGui.QLabel()
        self.filesize_warning.setStyleSheet('padding: 10px 0; font-weight: bold; color: #333333;')
        self.filesize_warning.hide()

        # downloads
        self.downloads = Downloads()

        # options
        self.options = Options(web)

        # status bar
        self.status_bar = QtGui.QStatusBar()
        self.status_bar.setSizeGripEnabled(False)

        # main layout
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(self.file_selection)
        self.layout.addLayout(self.server_status)
        self.layout.addWidget(self.filesize_warning)
        self.layout.addLayout(self.downloads)
        self.layout.addLayout(self.options)
        self.layout.addWidget(self.status_bar)
        self.setLayout(self.layout)
        self.show()

        # check for requests frequently
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.check_for_requests)
        self.timer.start(500)

    def start_server_step2(self):
        self.status_bar.showMessage(strings._('gui_starting_server3', True))

        # warn about sending large files over Tor
        if web.zip_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

    def start_server(self):
        # start the hidden service
        self.status_bar.showMessage(strings._('gui_starting_server1', True))
        try:
            self.app.choose_port()
            print strings._("connecting_ctrlport").format(int(self.app.port))
            self.app.start_hidden_service(gui=True)
        except onionshare.NoTor as e:
            alert(e.args[0], QtGui.QMessageBox.Warning)
            self.server_status.stop_server()
            self.status_bar.clearMessage()
            return
        except onionshare.TailsError as e:
            alert(e.args[0], QtGui.QMessageBox.Warning)
            self.server_status.stop_server()
            self.status_bar.clearMessage()
            return

        # start onionshare service in new thread
        t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open))
        t.daemon = True
        t.start()

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            web.set_file_info(self.file_selection.file_list.filenames)
            self.app.cleanup_filenames.append(web.zip_filename)
            self.starting_server_step2.emit()

            # wait for hs
            self.app.wait_for_hs()

            # done
            self.start_server_finished.emit()

        self.status_bar.showMessage(strings._('gui_starting_server2', True))
        t = threading.Thread(target=finish_starting_server, kwargs={'self': self})
        t.daemon = True
        t.start()

    def stop_server(self):
        if self.server_status.status == self.server_status.STATUS_STARTED:
            web.stop(self.app.port)
        self.app.cleanup()
        self.filesize_warning.hide()
        self.stop_server_finished.emit()

    def check_for_requests(self):
        self.update()
        # only check for requests if the server is running
        if self.server_status.status != self.server_status.STATUS_STARTED:
            return

        events = []

        done = False
        while not done:
            try:
                r = web.q.get(False)
                events.append(r)
            except web.Queue.Empty:
                done = True

        for event in events:
            if event["type"] == web.REQUEST_LOAD:
                self.status_bar.showMessage(strings._('download_page_loaded', True))

            elif event["type"] == web.REQUEST_DOWNLOAD:
                self.downloads.add_download(event["data"]["id"], web.zip_filesize)

            elif event["type"] == web.REQUEST_PROGRESS:
                self.downloads.update_download(event["data"]["id"], web.zip_filesize, event["data"]["bytes"])

                # is the download complete?
                if event["data"]["bytes"] == web.zip_filesize:
                    # close on finish?
                    if not web.get_stay_open():
                        self.server_status.stop_server()

            elif event["type"] == web.REQUEST_CANCELED:
                self.downloads.cancel_download(event["data"]["id"])

            elif event["path"] != '/favicon.ico':
                self.status_bar.showMessage('{0:s}: {1:s}'.format(strings._('other_page_loaded', True), event["path"]))

    def copy_url(self):
        self.status_bar.showMessage(strings._('gui_copied_url', True), 2000)

    def clear_message(self):
        self.status_bar.clearMessage()


def alert(msg, icon=QtGui.QMessageBox.NoIcon):
    dialog = QtGui.QMessageBox()
    dialog.setWindowTitle("OnionShare")
    dialog.setWindowIcon(window_icon)
    dialog.setText(msg)
    dialog.setIcon(icon)
    dialog.exec_()


def main():
    strings.load_strings()

    # start the Qt app
    global qtapp
    qtapp = Application()

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('--filenames', metavar='filenames', nargs='+', help=strings._('help_filename'))
    args = parser.parse_args()

    filenames = args.filenames
    if filenames:
        for i in range(len(filenames)):
            filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    stay_open = bool(args.stay_open)
    debug = bool(args.debug)

    # create the onionshare icon
    global window_icon
    window_icon = QtGui.QIcon(common.get_image_path('logo.png'))

    # validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.exists(filename):
                alert(strings._("not_a_file", True).format(filename))
                valid = False
        if not valid:
            sys.exit()

    # start the onionshare app
    web.set_stay_open(stay_open)
    app = onionshare.OnionShare(debug, local_only, stay_open)

    # clean up when app quits
    def shutdown():
        app.cleanup()
    qtapp.connect(qtapp, QtCore.SIGNAL("aboutToQuit()"), shutdown)

    # launch the gui
    gui = OnionShareGui(qtapp, app)
    gui.send_files(filenames)

    # all done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
