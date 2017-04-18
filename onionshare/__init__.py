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

import os, sys, time, argparse, shutil, socket, threading

from . import strings, helpers, web
from .onion import *

class OnionShare(object):
    """
    OnionShare is the main application class. Pass in options and run
    start_onion_service and it will do the magic.
    """
    def __init__(self, onion, debug=False, local_only=False, stay_open=False):
        # The Onion object
        self.onion = onion

        self.hidserv_dir = None
        self.onion_host = None
        self.stealth = None

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []

        # debug mode
        if debug:
            web.debug_mode()

        # do not use tor -- for development
        self.local_only = local_only

        # automatically close when download is finished
        self.stay_open = stay_open

    def set_stealth(self, stealth):
        self.stealth = stealth
        self.onion.stealth = stealth

    def start_onion_service(self):
        """
        Start the onionshare onion service.
        """
        self.port = helpers.get_available_port(17600, 17650)

        if self.local_only:
            self.onion_host = '127.0.0.1:{0:d}'.format(self.port)
            return

        self.onion_host = self.onion.start_onion_service(self.port)

        if self.stealth:
            self.auth_string = self.onion.auth_string

    def cleanup(self):
        """
        Shut everything down and clean up temporary files, etc.
        """
        # cleanup files
        for filename in self.cleanup_filenames:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                shutil.rmtree(filename)
        self.cleanup_filenames = []

        # cleanup the onion
        if self.onion:
            self.onion.cleanup()


def main(cwd=None):
    """
    The main() function implements all of the logic that the command-line version of
    onionshare uses.
    """
    strings.load_strings(helpers)
    print(strings._('version_string').format(helpers.get_version()))

    # OnionShare CLI in OSX needs to change current working directory (#132)
    if helpers.get_platform() == 'Darwin':
        if cwd:
            os.chdir(cwd)

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--stealth', action='store_true', dest='stealth', help=strings._("help_stealth"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('filename', metavar='filename', nargs='+', help=strings._('help_filename'))
    args = parser.parse_args()

    filenames = args.filename
    for i in range(len(filenames)):
        filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    debug = bool(args.debug)
    stay_open = bool(args.stay_open)
    stealth = bool(args.stealth)

    # Validation
    valid = True
    for filename in filenames:
        if not os.path.exists(filename):
            print(strings._("not_a_file").format(filename))
            valid = False
    if not valid:
        sys.exit()

    # Start the Onion object
    onion = Onion()
    try:
        onion.connect()
    except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorNotSupported, BundledTorTimeout) as e:
        sys.exit(e.args[0])
    except KeyboardInterrupt:
        print("")
        sys.exit()

    # Start the onionshare app
    try:
        app = OnionShare(onion, debug, local_only, stay_open)
        app.set_stealth(stealth)
        app.start_onion_service()
    except KeyboardInterrupt:
        print("")
        sys.exit()

    # Prepare files to share
    print(strings._("preparing_files"))
    web.set_file_info(filenames)
    app.cleanup_filenames.append(web.zip_filename)

    # Warn about sending large files over Tor
    if web.zip_filesize >= 157286400:  # 150mb
        print('')
        print(strings._("large_filesize"))
        print('')

    # Start OnionShare http service in new thread
    t = threading.Thread(target=web.start, args=(app.port, app.stay_open))
    t.daemon = True
    t.start()

    try:  # Trap Ctrl-C
        # Wait for web.generate_slug() to finish running
        time.sleep(0.2)

        if(stealth):
            print(strings._("give_this_url_stealth"))
            print('http://{0:s}/{1:s}'.format(app.onion_host, web.slug))
            print(app.auth_string)
        else:
            print(strings._("give_this_url"))
            print('http://{0:s}/{1:s}'.format(app.onion_host, web.slug))
        print('')
        print(strings._("ctrlc_to_stop"))

        # Wait for app to close
        while t.is_alive():
            t.join()
            # Allow KeyboardInterrupt exception to be handled with threads
            # https://stackoverflow.com/questions/3788208/python-threading-ignores-keyboardinterrupt-exception
            time.sleep(100)
    except KeyboardInterrupt:
        web.stop(app.port)
    finally:
        # Shutdown
        app.cleanup()

if __name__ == '__main__':
    main()
