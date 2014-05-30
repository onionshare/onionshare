#!/usr/bin/env python

import time, Queue, thread, gtk, gobject, os, sys, webkit

def select_file():
    global filename, basename

    # was a filename passed in as an argument?
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        basename = os.path.basename(filename)
        return True

    # choose a file
    canceled = False
    chooser = gtk.FileChooserDialog(
        title="Choose a file to share",
        action=gtk.FILE_CHOOSER_ACTION_OPEN,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
        filename = chooser.get_filename()
        basename = os.path.basename(filename)
    elif response == gtk.RESPONSE_CANCEL:
        canceled = True
    chooser.destroy()

    return not canceled

def async_gtk_msg(fun):
    def worker((function, args, kwargs)):
        apply(function, args, kwargs)

    def fun2(*args, **kwargs):
        gobject.idle_add(worker, (fun, args, kwargs))

    return fun2

def sync_gtk_msg(fun):
    class NoResult: pass

    def worker((R, function, args, kwargs)):
        R.result = apply(function, args, kwargs)

    def fun2(*args, **kwargs):
        class R: result = NoResult
        gobject.idle_add(callable=worker, user_data=(R, fun, args, kwargs))
        while R.result is NoResult: time.sleep(0.01)
        return R.result

    return fun2

def launch_browser(quit_function=None, echo=True):
    window = gtk.Window()
    browser = webkit.WebView()

    box = gtk.VBox(homogeneous=False, spacing=0)
    window.add(box)

    if quit_function is not None:
        # file > quit menu
        file_menu = gtk.Menu()
        quit_item = gtk.MenuItem('Quit')
        accel_group = gtk.AccelGroup()
        quit_item.add_accelerator('activate', accel_group, ord('Q'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        window.add_accel_group(accel_group)
        file_menu.append(quit_item)
        quit_item.connect('activate', quit_function)
        quit_item.show()
        menu_bar = gtk.MenuBar()
        menu_bar.show()
        file_item = gtk.MenuItem('File')
        file_item.show()
        file_item.set_submenu(file_menu)
        menu_bar.append(file_item)

        box.pack_start(menu_bar, expand=False, fill=True, padding=0)

        window.connect('destroy', quit_function)

    box.pack_start(browser, expand=True, fill=True, padding=0)

    window.set_default_size(400, 400)
    window.show_all()

    message_queue = Queue.Queue()

    def title_changed(title):
        if title != 'null': message_queue.put(title)

    def callback_wrapper(widget, frame, title): callback(title)
    browser.connect('title-changed', callback_wrapper)

    browser.open('file://'+os.getcwd()+'/index.html')

    def web_recv():
        if message_queue.empty():
            return None
        else:
            msg = message_queue.get()
            if echo: print '>>>', msg
            return msg

    def web_send(msg):
        if echo: print '<<<', msg
        async_gtk_msg(browser.execute_script)(msg)

    return browser, web_recv, web_send


def start_gtk_thread():
    # Start GTK in its own thread:
    gtk.gdk.threads_init()
    thread.start_new_thread(gtk.main, ())

def kill_gtk_thread():
    async_gtk_msg(gtk.main_quit)()

def main():
    if not select_file():
        return

    launch_browser()
