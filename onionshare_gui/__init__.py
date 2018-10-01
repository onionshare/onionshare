# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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
import os
import sys
import platform
import argparse
import signal
from .widgets import Alert
from PyQt5 import QtCore, QtWidgets

from onionshare import strings
from onionshare.common import Common
from onionshare.onion import Onion
from onionshare.onionshare import OnionShare

from .onionshare_gui import OnionShareGui

class Application(QtWidgets.QApplication):
    """
    This is Qt's QApplication class. It has been overridden to support threads
    and the quick keyboard shortcut.
    """
    def __init__(self, common):
        if common.platform == 'Linux' or common.platform == 'BSD':
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
    common = Common()
    common.define_css()

    # Load the default settings and strings early, for the sake of being able to parse options.
    # These won't be in the user's chosen locale necessarily, but we need to parse them
    # early in order to even display the option to pass alternate settings (which might
    # contain a preferred locale).
    # If an alternate --config is passed, we'll reload strings later.
    common.load_settings()
    strings.load_strings(common)

    # Display OnionShare banner
    print(strings._('version_string').format(common.version))

    # Allow Ctrl-C to smoothly quit the program instead of throwing an exception
    # https://stackoverflow.com/questions/42814093/how-to-handle-ctrlc-in-python-app-with-pyqt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Start the Qt app
    global qtapp
    qtapp = Application(common)

    # Parse arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=48))
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('--filenames', metavar='filenames', nargs='+', help=strings._('help_filename'))
    parser.add_argument('--config', metavar='config', default=False, help=strings._('help_config'))
    args = parser.parse_args()

    filenames = args.filenames
    if filenames:
        for i in range(len(filenames)):
            filenames[i] = os.path.abspath(filenames[i])

    config = args.config
    if config:
        # Re-load the strings, in case the provided config has changed locale
        common.load_settings(config)
        strings.load_strings(common)

    local_only = bool(args.local_only)
    debug = bool(args.debug)

    # Debug mode?
    common.debug = debug

    # Validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.isfile(filename) and not os.path.isdir(filename):
                Alert(common, strings._("not_a_file").format(filename))
                valid = False
            if not os.access(filename, os.R_OK):
                Alert(common, strings._("not_a_readable_file").format(filename))
                valid = False
        if not valid:
            sys.exit()

    # Start the Onion
    onion = Onion(common)

    # Start the OnionShare app
    app = OnionShare(common, onion, local_only)

    # Launch the gui
    gui = OnionShareGui(common, onion, qtapp, app, filenames, config, local_only)

    # Clean up when app quits
    def shutdown():
        onion.cleanup()
        app.cleanup()
    qtapp.aboutToQuit.connect(shutdown)

    # All done
    sys.exit(qtapp.exec_())

if __name__ == '__main__':
    main()
