#!/usr/bin/env python

import Tkinter as tk, tkFont, tkFileDialog
import sys, os, subprocess, time
from Queue import Queue, Empty
from threading import Thread

class OnionShareGUI(object):
    def __init__(self):
        self.root = tk.Tk()

        # prepare GUI
        self.root.title('OnionShare')
        self.root.resizable(0, 0)
        self.create_widgets()
        self.root.grid()

        # select file
        if len(sys.argv) >= 2:
            self.filename = sys.argv[1]
        else:
            self.filename = tkFileDialog.askopenfilename(title="Choose a file to share", parent=self.root)
        self.basename = os.path.basename(self.filename)
        self.root.title('OnionShare - {0}'.format(self.basename))

        # launch onionshare
        # trying to do this https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
        self.onionshare_bin = os.path.dirname(__file__)+'/onionshare.py'
        ON_POSIX = 'posix' in sys.builtin_module_names
        self.p = subprocess.Popen([self.onionshare_bin, self.filename], stdout=subprocess.PIPE, bufsize=1)
        self.q = Queue()
        self.t = Thread(target=self.enqueue_output, args=(self.p.stdout, self.q))
        self.t.daemon = True
        self.t.start()

        # update regularly
        self.update()

    def create_widgets(self):
        self.pad = 10
        sys12 = tkFont.Font(family="system", size=12)
        sys20 = tkFont.Font(family="system", size=20, weight="bold")

        # url
        self.url_labelframe = tk.LabelFrame(text="Send this URL to your friend")
        self.url_labelframe.pack()
        self.url_text = tk.Text(self.url_labelframe, width=31, height=2, font=sys20)
        self.url_text.config(state=tk.DISABLED)
        self.url_text.pack(padx=self.pad, pady=self.pad)
        self.url_labelframe.grid(padx=self.pad, pady=self.pad)

        # logs
        self.logs_labelframe = tk.LabelFrame(text="Server logs")
        self.logs_labelframe.pack()
        self.logs_text = tk.Text(self.logs_labelframe, width=70, height=10, font=sys12)
        self.logs_text.insert(tk.INSERT, "")
        self.logs_text.config(state=tk.DISABLED)
        self.logs_text.pack(padx=self.pad, pady=self.pad)
        self.logs_labelframe.grid(padx=self.pad, pady=self.pad)

        # quit button
        self.quit_button = tk.Button(self.root, text='Quit', command=self.root.quit)
        self.quit_button.grid(padx=self.pad, pady=self.pad)

    def update(self):
        """try:
            line = self.q.get_nowait()
        except Empty:
            pass
        else:
            print line"""

        # wait until the URL gets outputed
        """self.url = None
        while not self.url:
            line = self.p.stdout.readline()
            print line
            if line[:7] == 'http://':
                self.url = line
                self.url_text.insert(tk.INSERT, self.url)
            self.logs_text.insert(tk.INSERT, line)"""


        self.root.after(500, self.update)

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

if __name__ == '__main__':
    app = OnionShareGUI()
    app.root.mainloop()
