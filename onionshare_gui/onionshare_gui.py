from __future__ import division
import os, sys, subprocess, inspect, platform, argparse, threading, time, math, inspect, platform
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

    def start_send(self, filenames=None):
        # file selection
        file_selection = FileSelection()
        if filenames:
            for filename in filenames:
                file_selection.file_list.add_file(filename)

        # server status
        server_status = ServerStatus(file_selection)
        server_status.server_started.connect(file_selection.server_started)
        server_status.server_stopped.connect(file_selection.server_stopped)
        file_selection.file_list.files_updated.connect(server_status.update)

        # downloads
        downloads = Downloads()

        # options
        options = Options()

        # main layout
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(file_selection)
        self.layout.addLayout(server_status)
        self.layout.addLayout(downloads)
        self.layout.addLayout(options)
        self.setLayout(self.layout)
        self.show()

"""
        # initialize ui
        self.init_ui(filename, basename)
        # check for requests every 1000ms
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.check_for_requests)
        self.timer.start(1000)
        # copy url to clipboard
        self.copy_to_clipboard()

    def init_ui(self, filename, basename):
        # window
        self.setWindowTitle(u"{0} | OnionShare".format(basename.decode("utf-8")))
        self.resize(580, 400)
        self.setMinimumSize(580, 400)
        self.setMaximumSize(580, 400)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.white)
        self.setPalette(palette)

        # icon
        self.setWindowIcon(window_icon)

        # widget
        self.widget = QtGui.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(5, 5, 570, 390))

        # wrapper
        self.wrapper = QtGui.QVBoxLayout(self.widget)
        self.wrapper.setMargin(0)
        self.wrapper.setObjectName("wrapper")

        # header
        self.header = QtGui.QHBoxLayout()

        # logo
        self.logoLabel = QtGui.QLabel(self.widget)
        self.logo = QtGui.QPixmap("{0}/static/logo.png".format(common.onionshare_gui_dir))
        self.logoLabel.setPixmap(self.logo)
        self.header.addWidget(self.logoLabel)

        # fileinfo
        self.fileinfo = QtGui.QVBoxLayout()

        # filename
        self.filenameLabel = QtGui.QLabel(self.widget)
        self.filenameLabel.setStyleSheet("font-family: sans-serif; font-size: 22px; font-weight: bold; color: #000000; white-space: nowrap")
        self.filenameLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.fileinfo.addWidget(self.filenameLabel)

        # checksum
        self.checksumLabel = QtGui.QLabel(self.widget)
        self.checksumLabel.setStyleSheet("font-family: arial; text-align: left; color: #666666")
        self.checksumLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.fileinfo.addWidget(self.checksumLabel)

        # filesize
        self.filesizeLabel = QtGui.QLabel(self.widget)
        self.filesizeLabel.setStyleSheet("font-family: arial; text-align: left; color: #666666")
        self.filesizeLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.fileinfo.addWidget(self.filesizeLabel)
        self.header.addLayout(self.fileinfo)

        fileinfoSpacer = QtGui.QSpacerItem(20, 50, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        self.header.addItem(fileinfoSpacer)
        self.wrapper.addLayout(self.header)

        # header seperator
        self.headerSeperator = QtGui.QFrame(self.widget)
        self.headerSeperator.setFrameShape(QtGui.QFrame.HLine)
        self.headerSeperator.setFrameShadow(QtGui.QFrame.Plain)
        self.wrapper.addWidget(self.headerSeperator)

        # log
        self.log = QtGui.QVBoxLayout()
        self.log.setAlignment(QtCore.Qt.AlignTop)
        self.wrapper.addLayout(self.log)
        spacerItem2 = QtGui.QSpacerItem(1, 400, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        self.wrapper.addItem(spacerItem2)

        # footer seperator
        self.footerSeperator = QtGui.QFrame(self.widget)
        self.footerSeperator.setFrameShape(QtGui.QFrame.HLine)
        self.footerSeperator.setFrameShadow(QtGui.QFrame.Plain)
        self.wrapper.addWidget(self.footerSeperator)

        # footer
        self.footer = QtGui.QHBoxLayout()

        # close automatically checkbox
        self.closeAutomatically = QtGui.QCheckBox(self.widget)
        self.closeAutomatically.setCheckState(QtCore.Qt.Checked)
        if web.get_stay_open():
            self.closeAutomatically.setCheckState(QtCore.Qt.Unchecked)

        self.closeAutomatically.setStyleSheet("font-size: 12px")
        self.connect(self.closeAutomatically, QtCore.SIGNAL('stateChanged(int)'), self.stay_open_changed)
        self.footer.addWidget(self.closeAutomatically)

        # footer spacer
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.footer.addItem(spacerItem1)

        # copy url button
        self.copyURL = QtGui.QPushButton(self.widget)
        self.connect(self.copyURL, QtCore.SIGNAL("clicked()"), self.copy_to_clipboard)

        self.footer.addWidget(self.copyURL)
        self.wrapper.addLayout(self.footer)

        url = 'http://{0}/{1}'.format(self.app.onion_host, web.slug)

        filehash, filesize = helpers.file_crunching(filename)
        web.set_file_info(filename, filehash, filesize)

        # start onionshare service in new thread
        t = threading.Thread(target=web.start, args=(self.app.port, self.app.stay_open))
        t.daemon = True
        t.start()

        # show url to share
        loaded = QtGui.QLabel(strings._("give_this_url") + "<br /><strong>" + url + "</strong>")
        loaded.setStyleSheet("color: #000000; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
        loaded.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.log.addWidget(loaded)

        # translate
        self.filenameLabel.setText(basename)
        self.checksumLabel.setText(strings._("sha1_checksum") + ": <strong>" + filehash + "</strong>")
        self.filesizeLabel.setText(strings._("filesize") + ": <strong>" + helpers.human_readable_filesize(filesize) + "</strong>")
        self.closeAutomatically.setText(strings._("close_on_finish"))
        self.copyURL.setText(strings._("copy_url"))

        # show dialog
        self.show()

    def update_log(self, event, msg):
        global progress
        if event["type"] == web.REQUEST_LOAD:
            label = QtGui.QLabel(msg)
            label.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(label)
        elif event["type"] == web.REQUEST_DOWNLOAD:
            download = QtGui.QLabel(msg)
            download.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            download.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(download)
            progress = QtGui.QLabel()
            progress.setStyleSheet("color: #0000cc; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            progress.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(progress)
        elif event["type"] == web.REQUEST_PROGRESS:
            progress.setText(msg)
        elif event["path"] != '/favicon.ico':
            other = QtGui.QLabel(msg)
            other.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            other.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(other)
        return

    def check_for_requests(self):
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
                self.update_log(event, strings._("download_page_loaded"))
            elif event["type"] == web.REQUEST_DOWNLOAD:
                self.update_log(event, strings._("download_started"))
            elif event["type"] == web.REQUEST_PROGRESS:
                # is the download complete?
                if event["data"]["bytes"] == web.filesize:
                    self.update_log(event, strings._("download_finished"))
                    # close on finish?
                    if not web.get_stay_open():
                        time.sleep(1)
                        def close_countdown(i):
                            if i > 0:
                                QtGui.QApplication.quit()
                            else:
                                time.sleep(1)
                                i -= 1
                                closing.setText(strings._("close_countdown").format(str(i)))
                                print strings._("close_countdown").format(str(i))
                                close_countdown(i)

                        closing = QtGui.QLabel(self.widget)
                        closing.setStyleSheet("font-weight: bold; font-style: italic; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
                        closing.setText(strings._("close_countdown").format("3"))
                        closing.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                        self.log.addWidget(closing)
                        close_countdown(3)

                # still in progress
                else:
                    percent = math.floor((event["data"]["bytes"] / web.filesize) * 100)
                    self.update_log(event, " " + helpers.human_readable_filesize(event["data"]["bytes"]) + ', ' + str(percent) +'%')

            elif event["path"] != '/favicon.ico':
                self.update_log(event, strings._("other_page_loaded"))

    def copy_to_clipboard(self):
        url = 'http://{0}/{1}'.format(self.app.onion_host, web.slug)

        if platform.system() == 'Windows':
            # Qt's QClipboard isn't working in Windows
            # https://github.com/micahflee/onionshare/issues/46
            import ctypes
            GMEM_DDESHARE = 0x2000
            ctypes.windll.user32.OpenClipboard(None)
            ctypes.windll.user32.EmptyClipboard()
            hcd = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(url))+1)
            pch_data = ctypes.windll.kernel32.GlobalLock(hcd)
            ctypes.cdll.msvcrt.strcpy(ctypes.c_char_p(pch_data), bytes(url))
            ctypes.windll.kernel32.GlobalUnlock(hcd)
            ctypes.windll.user32.SetClipboardData(1, hcd)
            ctypes.windll.user32.CloseClipboard()
        else:
            clipboard = qtapp.clipboard()
            clipboard.setText(url)

        copied = QtGui.QLabel(strings._("copied_url"))
        copied.setStyleSheet("font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
        copied.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.log.addWidget(copied)
        return

    def stay_open_changed(self, state):
        if state > 0:
            web.set_stay_open(False)
        else:
            web.set_stay_open(True)
        return
"""

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

    """try:
        app.start_hidden_service(gui=True)
    except onionshare.NoTor as e:
        alert(e.args[0], QtGui.QMessageBox.Warning)
        sys.exit()
    except onionshare.TailsError as e:
        alert(e.args[0], QtGui.QMessageBox.Warning)
        sys.exit()
    """

    # clean up when app quits
    def shutdown():
        app.cleanup()
    qtapp.connect(qtapp, QtCore.SIGNAL("aboutToQuit()"), shutdown)

    # launch the gui
    gui = OnionShareGui(app)
    gui.start_send(filenames)

    # all done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
