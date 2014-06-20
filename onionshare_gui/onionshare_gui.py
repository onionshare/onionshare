import onionshare, webapp
import os, sys, subprocess

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

class Application(QApplication):
    def __init__(self):
        platform = onionshare.get_platform()
        if platform == 'Tails' or platform == 'Linux':
            self.setAttribute(Qt.AA_X11InitThreads, True)

        QApplication.__init__(self, sys.argv)

class WebAppThread(QThread):
    def __init__(self, webapp_port):
        QThread.__init__(self)
        self.webapp_port = webapp_port

    def run(self):
        webapp.app.run(port=self.webapp_port)

class Window(QWebView):
    def __init__(self, basename, webapp_port):
        QWebView.__init__(self)
        self.setWindowTitle("{0} | OnionShare".format(basename))
        self.resize(580, 400)
        self.setMinimumSize(580, 400)
        self.setMaximumSize(580, 400)
        self.load(QUrl("http://127.0.0.1:{0}".format(webapp_port)))

def alert(msg, icon=QMessageBox.NoIcon):
    dialog = QMessageBox()
    dialog.setWindowTitle("OnionShare")
    dialog.setText(msg)
    dialog.setIcon(icon)
    dialog.exec_()

def select_file(strings):
    # get filename, either from argument or file chooser dialog
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        args = {}
        if onionshare.get_platform() == 'Tails':
            args['directory'] = '/home/amnesia'

        filename = QFileDialog.getOpenFileName(caption=strings['choose_file'], options=QFileDialog.ReadOnly, **args)
        if not filename:
            return False, False

        filename = str(filename)

    # validate filename
    if not os.path.isfile(filename):
        alert(strings["not_a_file"].format(filename), QMessageBox.Warning)
        return False, False

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    return filename, basename

def main():
    onionshare.strings = onionshare.load_strings()

    # start the Qt app
    app = Application()

    # check for root in Tails
    if onionshare.get_platform() == 'Tails' and not onionshare.is_root():
        subprocess.call(['/usr/bin/gksudo']+sys.argv)
        return

    # try starting hidden service
    onionshare_port = onionshare.choose_port()
    try:
        onion_host = onionshare.start_hidden_service(onionshare_port)
    except onionshare.NoTor as e:
        alert(e.args[0], QMessageBox.Warning)
        return
    onionshare.tails_open_port(onionshare_port)

    # select file to share
    filename, basename = select_file(onionshare.strings)
    if not filename:
        return

    # initialize the web app
    webapp.onionshare = onionshare
    webapp.onionshare_port = onionshare_port
    webapp.filename = filename
    webapp.onion_host = onion_host
    webapp.qtapp = app
    webapp.clipboard = app.clipboard()

    # run the web app in a new thread
    webapp_port = onionshare.choose_port()
    onionshare.tails_open_port(webapp_port)
    webapp_thread = WebAppThread(webapp_port)
    webapp_thread.start()

    # clean up when app quits
    def shutdown():
        onionshare.tails_close_port(onionshare_port)
        onionshare.tails_close_port(webapp_port)
    app.connect(app, SIGNAL("aboutToQuit()"), shutdown)

    # launch the window
    web = Window(basename, webapp_port)
    web.show()

    # all done
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
