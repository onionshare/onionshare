import onionshare, webapp
import threading, os, sys, subprocess

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

qtapp = QApplication(sys.argv)

def alert(msg, icon=QMessageBox.NoIcon):
    dialog = QMessageBox()
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

def start_webapp(webapp_port, onionshare_port, filename, onion_host):
    global qtapp

    webapp.onionshare = onionshare
    webapp.onionshare_port = onionshare_port
    webapp.filename = filename
    webapp.onion_host = onion_host

    webapp.qtapp = qtapp
    webapp.clipboard = qtapp.clipboard()

    webapp.app.run(port=webapp_port)

def launch_window(webapp_port, onionshare_port, basename):
    def shutdown():
        onionshare.tails_close_port(onionshare_port)
        onionshare.tails_close_port(webapp_port)

    global qtapp
    qtapp.connect(qtapp, SIGNAL("aboutToQuit()"), shutdown)
    web = QWebView()
    web.load(QUrl("http://127.0.0.1:{0}".format(webapp_port)))
    web.show()
    sys.exit(qtapp.exec_())

    # todo: set window title, and do resizable stuff

def main():
    onionshare.strings = onionshare.load_strings()

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

    # start the gui web server
    webapp_port = onionshare.choose_port()
    t = threading.Thread(target=start_webapp, kwargs={
        'webapp_port': webapp_port,
        'onionshare_port': onionshare_port,
        'filename': filename,
        'onion_host': onion_host
    })
    t.daemon = True
    t.start()
    onionshare.tails_open_port(webapp_port)

    # launch the window
    launch_window(webapp_port, onionshare_port, basename)

if __name__ == '__main__':
    main()
