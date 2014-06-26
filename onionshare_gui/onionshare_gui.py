import os, sys, subprocess, inspect, platform, argparse
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

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
import webapp

window_icon = None

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
        global window_icon
        QWebView.__init__(self)
        self.setWindowTitle("{0} | OnionShare".format(basename))
        self.resize(580, 400)
        self.setMinimumSize(580, 400)
        self.setMaximumSize(580, 400)
        self.setWindowIcon(window_icon)
        self.load(QUrl("http://127.0.0.1:{0}".format(webapp_port)))

def alert(msg, icon=QMessageBox.NoIcon):
    global window_icon
    dialog = QMessageBox()
    dialog.setWindowTitle("OnionShare")
    dialog.setWindowIcon(window_icon)
    dialog.setText(msg)
    dialog.setIcon(icon)
    dialog.exec_()

def select_file(strings, filename=None):
    # get filename, either from argument or file chooser dialog
    if not filename:
        args = {}
        if onionshare.get_platform() == 'Tails':
            args['directory'] = '/home/amnesia'

        filename = QFileDialog.getOpenFileName(caption=translated('choose_file'), options=QFileDialog.ReadOnly, **args)
        if not filename:
            return False, False

        filename = str(filename)

    # validate filename
    if not os.path.isfile(filename):
        alert(translated("not_a_file").format(filename), QMessageBox.Warning)
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

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help='Do not attempt to use tor: for development only')
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help='Keep hidden service running after download has finished')
    parser.add_argument('--debug', action='store_true', dest='debug', help='Log errors to disk')
    parser.add_argument('filename', nargs='?', help='File to share')
    args = parser.parse_args()

    filename = args.filename
    local_only = args.local_only
    stay_open = bool(args.stay_open)
    debug = args.debug

    onionshare.set_stay_open(stay_open)

    # create the onionshare icon
    global window_icon, onionshare_gui_dir
    window_icon = QIcon("{0}/onionshare-icon.png".format(onionshare_gui_dir))

    # try starting hidden service
    onionshare_port = onionshare.choose_port()
    local_host = "127.0.0.1:{0}".format(onionshare_port)
    if not local_only:
        try:
            onion_host = onionshare.start_hidden_service(onionshare_port)
        except onionshare.NoTor as e:
            alert(e.args[0], QMessageBox.Warning)
            return
    onionshare.tails_open_port(onionshare_port)

    # select file to share
    filename, basename = select_file(onionshare.strings, filename)
    if not filename:
        return

    # initialize the web app
    webapp.onionshare = onionshare
    webapp.onionshare_port = onionshare_port
    webapp.filename = filename
    if not local_only:
        webapp.onion_host = onion_host
    else:
        webapp.onion_host = local_host
    webapp.qtapp = app
    webapp.clipboard = app.clipboard()
    webapp.stay_open = stay_open
    webapp.debug = debug

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
