import os
import sys
import json
import locale
import subprocess
import urllib
import gi
gi.require_version('Nautilus', '3.0')

from gi.repository import Nautilus
from gi.repository import GObject

# Put me in /usr/share/nautilus-python/extensions/
class OnionShareExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        # Get the localized string for "Share via OnionShare" label
        self.label = None
        default_label = 'Share via OnionShare'

        try:
            # Re-implement localization in python2
            default_locale = 'en'
            locale_dir = os.path.join(sys.prefix, 'share/onionshare/locale')
            if os.path.exists(locale_dir):
                # Load all translations
                strings = {}
                translations = {}
                for filename in os.listdir(locale_dir):
                    abs_filename = os.path.join(locale_dir, filename)
                    lang, ext = os.path.splitext(filename)
                    if ext == '.json':
                        with open(abs_filename) as f:
                            translations[lang] = json.load(f)

                strings = translations[default_locale]
                lc, enc = locale.getdefaultlocale()
                if lc:
                    lang = lc[:2]
                    if lang in translations:
                        # if a string doesn't exist, fallback to English
                        for key in translations[default_locale]:
                            if key in translations[lang]:
                                strings[key] = translations[lang][key]

                self.label = strings['share_via_onionshare']

        except:
            self.label = default_label

        if not self.label:
            self.label = default_label

        """
        # This more elegant solution will only work if nautilus is using python3, and onionshare is installed system-wide.
        # But nautilus is using python2, so this is commented out.
        try:
            import onionshare
            onionshare.strings.load_strings(onionshare.common)
            self.label = onionshare.strings._('share_via_onionshare')
        except:
            import sys
            print('python version: {}').format(sys.version)
            self.label = 'Share via OnionShare'
        """

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
                                         label=self.label,
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
