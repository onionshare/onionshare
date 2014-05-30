#!/usr/bin/env python

import onionshare, webgui
import signal, os, time, json

class Global(object):
    quit = False
    @classmethod
    def set_quit(cls, *args, **kwargs):
        cls.quit = True

def main():
    if not webgui.select_file():
        return

    webgui.start_gtk_thread()
    browser, web_recv, web_send = webgui.sync_gtk_msg(webgui.launch_browser)(quit_function=Global.set_quit)

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

        if msg == "got-a-click":
            clicks += 1
            web_send('document.getElementById("messages").innerHTML = %s' %
                     to_json('%d clicks so far' % clicks))
            # If you are using jQuery, you can do this instead:
            # web_send('$("#messages").text(%s)' %
            #          to_json('%d clicks so far' % clicks))

        if current_time - last_second >= 1.0:
            web_send('document.getElementById("uptime-value").innerHTML = %s' %
                     json.dumps('%d' % uptime_seconds))
            # If you are using jQuery, you can do this instead:
            # web_send('$("#uptime-value").text(%s)'
            #        % to_json('%d' % uptime_seconds))
            uptime_seconds += 1
            last_second += 1.0


        if again:
            pass
        else:
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
