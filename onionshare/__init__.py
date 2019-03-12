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

import os, sys, time, argparse, threading

from . import strings
from .common import Common
from .web import Web
from .onion import *
from .onionshare import OnionShare

def main(cwd=None):
    """
    The main() function implements all of the logic that the command-line version of
    onionshare uses.
    """
    common = Common()

    # Load the default settings and strings early, for the sake of being able to parse options.
    # These won't be in the user's chosen locale necessarily, but we need to parse them
    # early in order to even display the option to pass alternate settings (which might
    # contain a preferred locale).
    # If an alternate --config is passed, we'll reload strings later.
    common.load_settings()
    strings.load_strings(common)

    # Display OnionShare banner
    print(strings._('version_string').format(common.version))

    # OnionShare CLI in OSX needs to change current working directory (#132)
    if common.platform == 'Darwin':
        if cwd:
            os.chdir(cwd)

    # Parse arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=28))
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--shutdown-timeout', metavar='<int>', dest='shutdown_timeout', default=0, help=strings._("help_shutdown_timeout"))
    parser.add_argument('--connect-timeout', metavar='<int>', dest='connect_timeout', default=120, help=strings._("help_connect_timeout"))
    parser.add_argument('--stealth', action='store_true', dest='stealth', help=strings._("help_stealth"))
    parser.add_argument('--receive', action='store_true', dest='receive', help=strings._("help_receive"))
    parser.add_argument('--config', metavar='config', default=False, help=strings._('help_config'))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('filename', metavar='filename', nargs='*', help=strings._('help_filename'))
    args = parser.parse_args()

    filenames = args.filename
    for i in range(len(filenames)):
        filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    debug = bool(args.debug)
    stay_open = bool(args.stay_open)
    shutdown_timeout = int(args.shutdown_timeout)
    connect_timeout = int(args.connect_timeout)
    stealth = bool(args.stealth)
    receive = bool(args.receive)
    config = args.config

    if receive:
        mode = 'receive'
    else:
        mode = 'share'

    # Make sure filenames given if not using receiver mode
    if mode == 'share' and len(filenames) == 0:
        parser.print_help()
        sys.exit()

    # Validate filenames
    if mode == 'share':
        valid = True
        for filename in filenames:
            if not os.path.isfile(filename) and not os.path.isdir(filename):
                print(strings._("not_a_file").format(filename))
                valid = False
            if not os.access(filename, os.R_OK):
                print(strings._("not_a_readable_file").format(filename))
                valid = False
        if not valid:
            sys.exit()

    # Re-load settings, if a custom config was passed in
    if config:
        common.load_settings(config)
        # Re-load the strings, in case the provided config has changed locale
        strings.load_strings(common)

    # Debug mode?
    common.debug = debug

    # Create the Web object
    web = Web(common, False, mode)

    # Start the Onion object
    onion = Onion(common)
    try:
        onion.connect(custom_settings=False, config=config, connect_timeout=connect_timeout)
    except KeyboardInterrupt:
        print("")
        sys.exit()
    except Exception as e:
        sys.exit(e.args[0])

    # Start the onionshare app
    try:
        app = OnionShare(common, onion, local_only, shutdown_timeout)
        app.set_stealth(stealth)
        app.choose_port()
        app.start_onion_service()
    except KeyboardInterrupt:
        print("")
        sys.exit()
    except (TorTooOld, TorErrorProtocolError) as e:
        print("")
        print(e.args[0])
        sys.exit()

    if mode == 'share':
        # Prepare files to share
        print(strings._("preparing_files"))
        try:
            web.share_mode.set_file_info(filenames)
            app.cleanup_filenames += web.share_mode.cleanup_filenames
        except OSError as e:
            print(e.strerror)
            sys.exit(1)

        # Warn about sending large files over Tor
        if web.share_mode.download_filesize >= 157286400:  # 150mb
            print('')
            print(strings._("large_filesize"))
            print('')

    # Start OnionShare http service in new thread
    t = threading.Thread(target=web.start, args=(app.port, stay_open, common.settings.get('public_mode'), common.settings.get('slug')))
    t.daemon = True
    t.start()

    try:  # Trap Ctrl-C
        # Wait for web.generate_slug() to finish running
        time.sleep(0.2)

        # start shutdown timer thread
        if app.shutdown_timeout > 0:
            app.shutdown_timer.start()

        # Save the web slug if we are using a persistent private key
        if common.settings.get('save_private_key'):
            if not common.settings.get('slug'):
                common.settings.set('slug', web.slug)
                common.settings.save()

        # Build the URL
        if common.settings.get('public_mode'):
            url = 'http://{0:s}'.format(app.onion_host)
        else:
            url = 'http://{0:s}/{1:s}'.format(app.onion_host, web.slug)

        print('')
        if mode == 'receive':
            print(strings._('receive_mode_data_dir').format(common.settings.get('data_dir')))
            print('')
            print(strings._('receive_mode_warning'))
            print('')

            if stealth:
                print(strings._("give_this_url_receive_stealth"))
                print(url)
                print(app.auth_string)
            else:
                print(strings._("give_this_url_receive"))
                print(url)
        else:
            if stealth:
                print(strings._("give_this_url_stealth"))
                print(url)
                print(app.auth_string)
            else:
                print(strings._("give_this_url"))
                print(url)
        print('')
        print(strings._("ctrlc_to_stop"))

        # Wait for app to close
        while t.is_alive():
            if app.shutdown_timeout > 0:
                # if the shutdown timer was set and has run out, stop the server
                if not app.shutdown_timer.is_alive():
                    if mode == 'share':
                        # If there were no attempts to download the share, or all downloads are done, we can stop
                        if web.share_mode.download_count == 0 or web.done:
                            print(strings._("close_on_timeout"))
                            web.stop(app.port)
                            break
                    if mode == 'receive':
                        if web.receive_mode.upload_count == 0 or not web.receive_mode.uploads_in_progress:
                            print(strings._("close_on_timeout"))
                            web.stop(app.port)
                            break
                        else:
                            web.receive_mode.can_upload = False
            # Allow KeyboardInterrupt exception to be handled with threads
            # https://stackoverflow.com/questions/3788208/python-threading-ignores-keyboardinterrupt-exception
            time.sleep(0.2)
    except KeyboardInterrupt:
        web.stop(app.port)
    finally:
        # Shutdown
        app.cleanup()
        onion.cleanup()

if __name__ == '__main__':
    main()
