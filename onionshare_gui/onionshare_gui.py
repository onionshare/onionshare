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

    # send the browser initial data
    time.sleep(0.1)
    web_send("set_basename('{0}')".format(basename))

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

def my_quit_wrapper(fun):
    signal.signal(signal.SIGINT, Global.set_quit)
    def fun2(*args, **kwargs):
        try:
            x = fun(*args, **kwargs) # equivalent to "apply"
        finally:
            kill_gtk_thread()
            Global.set_quit()
        return x
    return fun2

if __name__ == '__main__':
    main()
