from __future__ import division
import os, sys, subprocess, inspect, platform, argparse, threading, time, math, inspect, platform, urllib2
from PyQt4 import QtCore, QtGui

import common

try:
    import onionshare
except ImportError:
    sys.path.append(os.path.abspath(common.onionshare_gui_dir+"/.."))
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

class OnionShareGui(QtGui.QWidget):
    def __init__(self, app):
        super(OnionShareGui, self).__init__()
        self.app = app

        self.setWindowTitle('OnionShare')
        self.setWindowIcon(window_icon)

    def send_files(self, filenames=None):
        # file selection
        file_selection = FileSelection()
        if filenames:
            for filename in filenames:
                file_selection.file_list.add_file(filename)

        # server status
        self.server_status = ServerStatus(file_selection)
        self.server_status.server_started.connect(file_selection.server_started)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_stopped.connect(file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.stop_server)
        file_selection.file_list.files_updated.connect(self.server_status.update)

        # downloads
        downloads = Downloads()

        # options
        options = Options(web.stay_open)

        # main layout
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(file_selection)
        self.layout.addLayout(self.server_status)
        self.layout.addLayout(downloads)
        self.layout.addLayout(options)
        self.setLayout(self.layout)
        self.show()

    def start_server(self):
        # start the hidden service
        try:
            self.app.start_hidden_service(gui=True)
        except onionshare.NoTor as e:
            alert(e.args[0], QtGui.QMessageBox.Warning)
            self.server_status.stop_server()
            return
        except onionshare.TailsError as e:
            alert(e.args[0], QtGui.QMessageBox.Warning)
            self.server_status.stop_server()
            return

        # start onionshare service in new thread
        t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open))
        t.daemon = True
        t.start()

    def stop_server(self):
        # to stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
        urllib2.urlopen('http://127.0.0.1:{0}/{1}/shutdown'.format(self.app.port, web.shutdown_slug)).read()

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

    # validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.exists(filename):
                alert(strings._("not_a_file").format(filename))
                valid = False
        if not valid:
            sys.exit()

    # create the onionshare icon
    global window_icon
    window_icon = QtGui.QIcon("{0}/static/logo.png".format(common.onionshare_gui_dir))

    # start the onionshare app
    web.set_stay_open(stay_open)
    app = onionshare.OnionShare(debug, local_only, stay_open)

    # clean up when app quits
    def shutdown():
        app.cleanup()
    qtapp.connect(qtapp, QtCore.SIGNAL("aboutToQuit()"), shutdown)

    # launch the gui
    gui = OnionShareGui(app)
    gui.send_files(filenames)

    # all done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
