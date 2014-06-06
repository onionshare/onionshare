#!/usr/bin/env python

import onionshare, webgui
import os, sys, time, json, gtk, gobject, thread

url = None

class Global(object):
    quit = False
    @classmethod
    def set_quit(cls, *args, **kwargs):
        cls.quit = True

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

def main():
    global url
    strings = onionshare.load_strings()

    # try starting hidden service
    port = onionshare.choose_port()
    try:
        onion_host = onionshare.start_hidden_service(port)
    except onionshare.NoTor as e:
        alert(e.args[0], gtk.MESSAGE_ERROR)
        return
    onionshare.tails_open_port(port)

    # select file to share
    filename, basename = select_file(strings)
    if not filename:
        return

    # open the window, launching webkit browser
    webgui.start_gtk_thread()
    browser, web_recv, web_send = webgui.sync_gtk_msg(webgui.launch_window)(
        title="OnionShare | {0}".format(basename),
        quit_function=Global.set_quit,
        echo=False)

    # clipboard
    clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
    def set_clipboard():
        global url
        clipboard.set_text(url)
        web_send("update('{0}')".format('Copied secret URL to clipboard.'))

    # the async nature of things requires startup to be split into multiple functions
    def startup_async():
        global url
        filehash, filesize = onionshare.file_crunching(filename)
        onionshare.set_file_info(filename, filehash, filesize)
        url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)
        web_send("update('{0}')".format(strings['give_this_url'].replace('\'', '\\\'')))
        web_send("update('<strong>{0}</strong>')".format(url))
        web_send("url_is_set()")

        # clipboard needs a bit of time before copying url
        gobject.timeout_add(500, set_clipboard)

    def startup_sync():
        web_send("init('{0}', {1});".format(basename, json.dumps(strings)))
        web_send("update('{0}')".format(strings['calculating_sha1']))

        # run other startup in the background
        thread_crunch = thread.start_new_thread(startup_async, ())

        # start the web server
        thread_web = thread.start_new_thread(onionshare.app.run, (), {"port": port})

    gobject.timeout_add(500, startup_sync)

    # main loop
    last_second = time.time()
    uptime_seconds = 1
    clicks = 0
    while not Global.quit:

        current_time = time.time()
        again = False
        msg = web_recv()
        if msg:
            again = True

        # check msg for messages from the browser
        if msg == 'copy_url':
            set_clipboard()

        if not again:
            time.sleep(0.1)

    # shutdown
    onionshare.tails_close_port(port)

if __name__ == '__main__':
    main()
