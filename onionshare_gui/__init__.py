# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division
import os, sys, platform, argparse
from .alert import Alert
from PyQt5 import QtCore, QtWidgets

from onionshare import strings, common, web
from onionshare.onion import Onion
from onionshare.onionshare import OnionShare
from onionshare.settings import Settings

from .onionshare_gui import OnionShareGui

class Application(QtWidgets.QApplication):
    """
    This is Qt's QApplication class. It has been overridden to support threads
    and the quick keyboard shortcut.
    """
    def __init__(self):
        system = platform.system()
        if system == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.key() == QtCore.Qt.Key_Q and
            event.modifiers() == QtCore.Qt.ControlModifier):
                self.quit()
        return False


def main():
    """
    The main() function implements all of the logic that the GUI version of onionshare uses.
    """
    strings.load_strings(common)
    print(strings._('version_string').format(common.get_version()))

    # Start the Qt app
    global qtapp
    qtapp = Application()

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--shutdown-timeout', metavar='shutdown_timeout', dest='shutdown_timeout', default=0, help=strings._("help_shutdown_timeout"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('--filenames', metavar='filenames', nargs='+', help=strings._('help_filename'))
    parser.add_argument('--config', metavar='config', default=False, help=strings._('help_config'))
    args = parser.parse_args()

    filenames = args.filenames
    if filenames:
        for i in range(len(filenames)):
            filenames[i] = os.path.abspath(filenames[i])

    config = args.config

    local_only = bool(args.local_only)
    stay_open = bool(args.stay_open)
    shutdown_timeout = float(args.shutdown_timeout)
    debug = bool(args.debug)

    # Debug mode?
    if debug:
        common.set_debug(debug)
        web.debug_mode()

    # Validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.exists(filename):
                Alert(strings._("not_a_file", True).format(filename))
                valid = False
            if not os.access(filename, os.R_OK):
                Alert(strings._("not_a_readable_file", True).format(filename))
                valid = False
        if not valid:
            sys.exit()

    # Start the Onion
    onion = Onion()

    # Start the OnionShare app
    web.set_stay_open(stay_open)
    app = OnionShare(onion, local_only, stay_open, shutdown_timeout)

    # Launch the gui
    gui = OnionShareGui(onion, qtapp, app, filenames, config)

    # Clean up when app quits
    def shutdown():
        onion.cleanup()
        app.cleanup()
    qtapp.aboutToQuit.connect(shutdown)

    # All done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
