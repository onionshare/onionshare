import onionshare, webapp
import threading, gtk, gobject, webkit, os, sys

def alert(msg, type=gtk.MESSAGE_INFO):
    dialog = gtk.MessageDialog(
        parent=None,
        flags=gtk.DIALOG_MODAL,
        type=type,
        buttons=gtk.BUTTONS_OK,
        message_format=msg)
    response = dialog.run()
    dialog.destroy()

def select_file(strings):
    # get filename, either from argument or file chooser dialog
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        canceled = False
        chooser = gtk.FileChooserDialog(
            title="Choose a file to share",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            canceled = True
        chooser.destroy()

        if canceled:
            return False, False

    # validate filename
    if not os.path.isfile(filename):
        alert(strings["not_a_file"].format(filename), gtk.MESSAGE_ERROR)
        return False, False

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    return filename, basename

def start_webapp(webapp_port, onionshare_port, filename, onion_host):
    webapp.onionshare = onionshare
    webapp.onionshare_port = onionshare_port
    webapp.filename = filename
    webapp.onion_host = onion_host
    webapp.app.run(port=webapp_port)

def launch_window(webapp_port, onionshare_port):
    def on_destroy(widget, data=None):
        onionshare.tails_close_port(onionshare_port)
        gtk.main_quit()

    window = gtk.Window()
    window.set_title('OnionShare')
    window.resize(550, 300)
    window.set_resizable(False)
    window.connect('destroy', on_destroy)

    box = gtk.VBox(homogeneous=False, spacing=0)
    window.add(box)

    browser = webkit.WebView()
    box.pack_start(browser, expand=True, fill=True, padding=0)

    window.show_all()

    # wait half a second for server to start
    gobject.timeout_add(500, browser.open, 'http://127.0.0.1:{0}/'.format(webapp_port))

    gtk.main()

def main():
    onionshare.strings = onionshare.load_strings()

    # try starting hidden service
    onionshare_port = onionshare.choose_port()
    try:
        onion_host = onionshare.start_hidden_service(onionshare_port)
    except onionshare.NoTor as e:
        alert(e.args[0], gtk.MESSAGE_ERROR)
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

    # launch the window
    launch_window(webapp_port, onionshare_port)

if __name__ == '__main__':
    main()
