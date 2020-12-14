# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2020 Micah Lee, et al. <micah@micahflee.com>

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
import json
import psutil
import getpass
from PySide2 import QtCore, QtWidgets

from onionshare_cli.common import Common

from .gui_common import GuiCommon
from .widgets import Alert
from .main_window import MainWindow


class Application(QtWidgets.QApplication):
    """
    This is Qt's QApplication class. It has been overridden to support threads
    and the quick keyboard shortcut.
    """

    def __init__(self, common):
        if common.platform == "Linux" or common.platform == "BSD":
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (
            event.type() == QtCore.QEvent.KeyPress
            and event.key() == QtCore.Qt.Key_Q
            and event.modifiers() == QtCore.Qt.ControlModifier
        ):
            self.quit()
        return False


def main():
    """
    The main() function implements all of the logic that the GUI version of onionshare uses.
    """
    common = Common()

    # Required for macOS Big Sur: https://stackoverflow.com/a/64878899
    if common.platform == "Darwin":
        os.environ["QT_MAC_WANTS_LAYER"] = "1"

    # Display OnionShare banner
    print(f"OnionShare {common.version} | https://onionshare.org/")

    # Start the Qt app
    global qtapp
    qtapp = Application(common)

    # Parse arguments
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=48)
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        dest="local_only",
        help="Don't use Tor (only for development)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Log OnionShare errors to stdout, and web errors to disk",
    )
    parser.add_argument(
        "--filenames",
        metavar="filenames",
        nargs="+",
        help="List of files or folders to share",
    )
    args = parser.parse_args()

    filenames = args.filenames
    if filenames:
        for i in range(len(filenames)):
            filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    verbose = bool(args.verbose)

    # Verbose mode?
    common.verbose = verbose

    # Attach the GUI common parts to the common object
    common.gui = GuiCommon(common, qtapp, local_only)

    # Validation
    if filenames:
        valid = True
        for filename in filenames:
            if not os.path.isfile(filename) and not os.path.isdir(filename):
                Alert(common, f"{filename} is not a valid file.")
                valid = False
            if not os.access(filename, os.R_OK):
                Alert(common, f"{filename} is not a readable file.")
                valid = False
        if not valid:
            sys.exit()

    # Is there another onionshare-gui running?
    if os.path.exists(common.gui.lock_filename):
        with open(common.gui.lock_filename, "r") as f:
            existing_pid = int(f.read())

        # Is this process actually still running?
        still_running = True
        if not psutil.pid_exists(existing_pid):
            still_running = False
        else:
            for proc in psutil.process_iter(["pid", "name", "username"]):
                if proc.pid == existing_pid:
                    if (
                        proc.username() != getpass.getuser()
                        or "onionshare" not in " ".join(proc.cmdline()).lower()
                    ):
                        still_running = False

        if still_running:
            print(f"Opening tab in existing OnionShare window (pid {existing_pid})")

            # Make an event for the existing OnionShare window
            if filenames:
                obj = {"type": "new_share_tab", "filenames": filenames}
            else:
                obj = {"type": "new_tab"}

            # Write that event to disk
            with open(common.gui.events_filename, "a") as f:
                f.write(json.dumps(obj) + "\n")
            return
        else:
            os.remove(common.gui.lock_filename)

    # Write the lock file
    with open(common.gui.lock_filename, "w") as f:
        f.write(f"{os.getpid()}\n")

    # Allow Ctrl-C to smoothly quit the program instead of throwing an exception
    def signal_handler(s, frame):
        print("\nCtrl-C pressed, quitting")
        if os.path.exists(common.gui.lock_filename):
            os.remove(common.gui.lock_filename)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Launch the gui
    main_window = MainWindow(common, filenames)

    # If filenames were passed in, open them in a tab
    if filenames:
        main_window.tabs.new_share_tab(filenames)

    # Clean up when app quits
    def shutdown():
        main_window.cleanup()
        os.remove(common.gui.lock_filename)

    qtapp.aboutToQuit.connect(shutdown)

    # All done
    sys.exit(qtapp.exec_())
