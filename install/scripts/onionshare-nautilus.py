#!/usr/bin/python2

import os
import subprocess
import urllib
import gi
gi.require_version('Nautilus', '3.0')

from gi.repository import Nautilus
from gi.repository import GObject

# Put me in /usr/share/nautilus-python/extensions/
class OnionShareExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    def url2path(self,url):
	file_uri = url.get_activation_uri()
        arg_uri = file_uri[7:]
        path = urllib.url2pathname(arg_uri)
        return path

    def exec_onionshare(self, filenames):
# Would prefer this method but there is a conflict between GTK 2.0 vs GTK 3.0 components being loaded at once
# (nautilus:3090): Gtk-ERROR **: GTK+ 2.x symbols detected. Using GTK+ 2.x and GTK+ 3 in the same process is not supported
#        sys.argv = ["", "--filenames"] + filenames
#        sys.exit(onionshare_gui.main())
        path = os.path.join(os.sep, 'usr', 'bin', 'onionshare-gui')
        cmd = [path, "--filenames"] + filenames
        subprocess.Popen(cmd)

    def get_file_items(self, window, files):
        menuitem = Nautilus.MenuItem(name='OnionShare::Nautilus',
                                         label='Share via OnionShare',
                                         tip='',
                                         icon='')
        menu = Nautilus.Menu()
        menu.append_item(menuitem)
        menuitem.connect("activate", self.menu_activate_cb, files)
        return menuitem,

    def menu_activate_cb(self, menu, files):
        file_list = []
        for file in files:
            file_list.append(self.url2path(file))
        self.exec_onionshare(file_list)
