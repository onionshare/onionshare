#!/usr/bin/env python

import onionshare, webgui
import signal, os, time, json

class Global(object):
    quit = False
    @classmethod
    def set_quit(cls, *args, **kwargs):
        cls.quit = True

def main():
    filename, basename = webgui.select_file()
    if not filename:
        return

    # open the window, launching webkit browser
    webgui.start_gtk_thread()
    browser, web_recv, web_send = webgui.sync_gtk_msg(webgui.launch_window)(
        title="OnionShare | {0}".format(basename),
        quit_function=Global.set_quit)

    # wait for window to render
    time.sleep(0.1)
    
    # initialize onionshare
    strings = onionshare.load_strings()
    web_send("init('{0}', {1});".format(basename, json.dumps(strings)))

    web_send("update('{0}')".format(strings['calculating_sha1']))
    filehash, filesize = onionshare.file_crunching(filename)
    port = onionshare.choose_port()
    
    web_send("update('{0}')".format(strings['connecting_ctrlport'].format(port)))
    onion_host = onionshare.start_hidden_service(port)

    # punch a hole in the firewall
    onionshare.tails_open_port(port)
    
    url = 'http://{0}/{1}'.format(onion_host, onionshare.slug)
    web_send("update('{0}')".format('Secret URL is {0}'.format(url)))
    web_send("set_url('{0}')".format(url));

    # start the web server
    # todo: start this in another thread, and send output using web_send
    #onionshare.app.run(port=port)

    # main loop
    last_second = time.time()
    uptime_seconds = 1
    clicks = 0
    while not Global.quit:

        current_time = time.time()
        again = False
        msg = web_recv()
        if msg:
            msg = json.loads(msg)
            again = True

        # check msg for messages from the browser
        # use web_send() to send javascript to the browser

        if not again:
            time.sleep(0.1)
    
    # shutdown
    onionshare.tails_close_port(port)

if __name__ == '__main__':
    main()
