from __future__ import division
import os, sys, subprocess, inspect, platform, argparse, threading, time, math
from PyQt4 import QtCore, QtGui

if platform.system() == 'Darwin':
    onionshare_gui_dir = os.path.dirname(__file__)
else:
    onionshare_gui_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

try:
    import onionshare
except ImportError:
    sys.path.append(os.path.abspath(onionshare_gui_dir+"/.."))
    import onionshare
from onionshare import translated

app = None
window_icon = None
onion_host = None
port = None
progress = None
gui = None

# request types
REQUEST_LOAD = 0
REQUEST_DOWNLOAD = 1
REQUEST_UPLOAD_DONE = 3
REQUEST_UPLOAD = 4
REQUEST_OTHER = 5

class Application(QtGui.QApplication):
    def __init__(self):
        platform = onionshare.get_platform()
        if platform == 'Tails' or platform == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtGui.QApplication.__init__(self, sys.argv)

class OnionShareGui(QtGui.QWidget):
    def __init__(self):
        super(OnionShareGui, self).__init__()
        # initialize ui
        # choose file or to receive
        self.filename = None
        self.save_dir = None
        self.basename = None
        self.send_or_receive()
        if not onionshare.onionshare.receive_allowed:
            self.filename, self.basename = select_file(onionshare.strings)
        else:
            self.save_dir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
            onionshare.onionshare.file_destination = self.save_dir
        onionshare_target = self.filename or self.save_dir
        basename = self.basename or "Receiver Mode"
        self.init_ui(onionshare_target, basename)
        # check for requests every 1000ms
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.check_for_requests)
        self.timer.start(1000)
        # copy url to clipboard
        self.copy_to_clipboard()

    def init_ui(self, filename, basename):
        # window
        self.setWindowTitle("{0} | OnionShare".format(basename))
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
        self.logo = QtGui.QPixmap("{0}/static/logo.png".format(onionshare_gui_dir))
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
        if onionshare.stay_open:
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

        if not onionshare.onionshare.receive_allowed:
            url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)
            filehash, filesize = onionshare.file_crunching(filename)
            onionshare.set_file_info(filename, filehash, filesize)
            onionshare.filesize = filesize
        else:
            url = 'http://{0}/send'.format(onion_host)


        # start onionshare service in new thread
        t = threading.Thread(target=onionshare.app.run, kwargs={'port': port})
        t.daemon = True
        t.start()

        # show url to share
        if not onionshare.onionshare.receive_allowed:
            loaded = QtGui.QLabel(translated("give_this_url") + "<br /><strong>" + url + "</strong>")
        else:
            loaded = QtGui.QLabel(translated("give_this_upload_url")+"<br /><strong>"+url+"</strong>")
        loaded.setStyleSheet("color: #000000; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
        loaded.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.log.addWidget(loaded)

        # translate
        if not onionshare.onionshare.receive_allowed:
            self.filenameLabel.setText(basename)
            self.checksumLabel.setText(translated("sha1_checksum") + ": <strong>" + filehash + "</strong>")
            self.filesizeLabel.setText(translated("filesize") + ": <strong>" + onionshare.human_readable_filesize(filesize) + "</strong>")
            self.closeAutomatically.setText(translated("close_on_finish"))
        else:
            self.closeAutomatically.setText(translated("accept_one_upload"))
        self.copyURL.setText(translated("copy_url"))

        # show dialog
        self.show()

    def update_log(self, event, msg):
        global progress
        if event["type"] == REQUEST_LOAD:
            label = QtGui.QLabel(msg)
            label.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(label)
        elif event["type"] == REQUEST_DOWNLOAD:
            download = QtGui.QLabel(msg)
            download.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            download.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(download)
            progress = QtGui.QLabel()
            progress.setStyleSheet("color: #0000cc; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            progress.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(progress)
        elif event["type"] == REQUEST_PROGRESS:
            progress.setText(msg)
        elif event["type"] == REQUEST_UPLOAD_DONE:
            filename = event["data"]["filename"]
            user_submitted_hash = event["data"]["hash"]
            filename_label = QtGui.QLabel(translated("submitted_filename")+filename)
            hash_label = QtGui.QLabel(translated("submitted_sha1_checksum")+user_submitted_hash)
            self.log.addWidget(filename_label)
            self.log.addWidget(hash_label)
        elif event["path"] != '/favicon.ico':
            other = QtGui.QLabel(msg)
            other.setStyleSheet("color: #009900; font-weight: bold; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
            other.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.log.addWidget(other)
        return

    def send_or_receive(self):
        prompt = translated("start_receiver_mode")
        response = QtGui.QMessageBox.question(self, "Startup", prompt, QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.No)

        if response == QtGui.QMessageBox.Yes:
            onionshare.onionshare.receive_allowed = True

    def check_for_requests(self):
        events = []

        done = False
        while not done:
            try:
                r = onionshare.q.get(False)
                events.append(r)
            except onionshare.Queue.Empty:
                done = True

        for event in events:
            if event["type"] == REQUEST_LOAD:
                self.update_log(event, translated("download_page_loaded"))
            elif event["type"] == REQUEST_DOWNLOAD:
                self.update_log(event, translated("download_started"))
            elif event["type"] == REQUEST_PROGRESS:
                # is the download complete?
                if event["data"]["bytes"] == onionshare.filesize:
                    self.update_log(event, translated("download_finished"))
                    # close on finish?
                    if not onionshare.stay_open:
                        time.sleep(1)
                        def close_countdown(i):
                            if i > 0:
                                QtGui.QApplication.quit()
                            else:
                                time.sleep(1)
                                i -= 1
                                closing.setText(translated("close_countdown").format(str(i)))
                                print translated("close_countdown").format(str(i))
                                close_countdown(i)

                        closing = QtGui.QLabel(self.widget)
                        closing.setStyleSheet("font-weight: bold; font-style: italic; font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
                        closing.setText(translated("close_countdown").format("3"))
                        closing.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                        self.log.addWidget(closing)
                        close_countdown(3)

                # still in progress
                else:
                    percent = math.floor((event["data"]["bytes"] / onionshare.filesize) * 100)
                    self.update_log(event, " " + onionshare.human_readable_filesize(event["data"]["bytes"]) + ', ' + str(percent) +'%')
            elif event["type"] == REQUEST_UPLOAD_DONE:
                self.update_log(event, '')
            elif event["path"] != '/favicon.ico':
                if event["path"] == '/send':
                    self.update_log(event, translated("upload_page_loaded"))
                else:
                    self.update_log(event, translated("other_page_loaded"))

    def copy_to_clipboard(self):
        global onion_host
        if not onionshare.onionshare.receive_allowed:
            url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)
        else:
            url = 'http://{0}/send'.format(onion_host)

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
            clipboard = app.clipboard()
            clipboard.setText(url)

        copied = QtGui.QLabel(translated("copied_url"))
        copied.setStyleSheet("font-size: 14px; padding: 5px 10px; border-bottom: 1px solid #cccccc;")
        copied.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.log.addWidget(copied)
        return

    def stay_open_changed(self, state):
        if state > 0:
            onionshare.set_stay_open(False)
        onionshare.set_stay_open(True)
        return

def alert(msg, icon=QtGui.QMessageBox.NoIcon):
    global window_icon
    dialog = QtGui.QMessageBox()
    dialog.setWindowTitle("OnionShare")
    dialog.setWindowIcon(window_icon)
    dialog.setText(msg)
    dialog.setIcon(icon)
    dialog.exec_()

def select_file(strings, filename=None):
    # get filename, either from argument or file chooser dialog
    if not filename:
        filename = QtGui.QFileDialog.getOpenFileName(caption=translated('choose_file'), options=QtGui.QFileDialog.ReadOnly)
        if not filename:
            return False, False

        filename = str(filename)

    # validate filename
    if not os.path.isfile(filename):
        alert(translated("not_a_file").format(filename), QtGui.QMessageBox.Warning)
        return False, False

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    return filename, basename

def main():
    global port
    onionshare.strings = onionshare.load_strings()

    # start the Qt app
    global app
    app = Application()

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=translated("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=translated("help_stay_open"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=translated("help_debug"))
    parser.add_argument('filename', nargs="?", help=translated("help_filename"))
    args = parser.parse_args()

    filename = args.filename
    local_only = bool(args.local_only)
    stay_open = bool(args.stay_open)
    debug = bool(args.debug)

    if debug:
        onionshare.debug_mode()

    onionshare.set_stay_open(stay_open)

    # create the onionshare icon
    global window_icon, onionshare_gui_dir
    window_icon = QtGui.QIcon("{0}/static/logo.png".format(onionshare_gui_dir))

    # try starting hidden service
    global onion_host
    port = onionshare.choose_port()
    local_host = "127.0.0.1:{0}".format(port)

    if onionshare.get_platform() == 'Tails':
        # if this is tails, start the root process
        root_p = subprocess.Popen(['/usr/bin/gksudo', '-D', 'OnionShare', '--', '/usr/bin/onionshare', str(port)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout = root_p.stdout.read(22) # .onion URLs are 22 chars long

        if stdout:
            onion_host = stdout
        else:
            if root_p.poll() == -1:
                alert(root_p.stderr.read())
                return
            else:
                alert(translated("error_tails_unknown_root"))
                return
    else:
        # if not tails, start hidden service normally
        if not local_only:
            try:
                onion_host = onionshare.start_hidden_service(port)
            except onionshare.NoTor as e:
                alert(e.args[0], QtGui.QMessageBox.Warning)
                return


    # clean up when app quits
    def shutdown():
        pass
    app.connect(app, QtCore.SIGNAL("aboutToQuit()"), shutdown)

    # launch the gui
    global gui
    gui = OnionShareGui()

    # all done
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
