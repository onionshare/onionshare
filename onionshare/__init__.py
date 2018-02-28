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

import os
import sys
import threading
import time
from argparse import ArgumentParser, FileType, HelpFormatter

from . import strings, common, web
from .onion import (
    BundledTorNotSupported,
    BundledTorTimeout,
    Onion,
    TorErrorAuthError,
    TorErrorAutomatic,
    TorErrorInvalidSetting,
    TorErrorMissingPassword,
    TorErrorProtocolError,
    TorErrorSocketFile,
    TorErrorSocketPort,
    TorErrorUnreadableCookieFile,
    TorTooOld
)
from .onionshare import OnionShare
from .settings import Settings


def _parse_cmdline_args():
    parser = ArgumentParser(
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=28))
    parser.add_argument(
        '--local-only', action='store_true',
        help=strings._("help_local_only"))
    parser.add_argument(
        '--stay-open', action='store_true',
        help=strings._("help_stay_open"))
    parser.add_argument(
        '--shutdown-timeout', metavar='<int>', default=0, type=int,
        help=strings._("help_shutdown_timeout"))
    parser.add_argument(
        '--stealth', action='store_true',
        help=strings._("help_stealth"))
    parser.add_argument(
        '--debug', action='store_true',
        help=strings._("help_debug"))
    parser.add_argument(
        '--config', metavar='config', default=False, type=FileType('r'),
        help=strings._('help_config'))
    parser.add_argument(
        'filename', metavar='filename', nargs='+', type=FileType('r'),
        help=strings._('help_filename'))
    return parser.parse_args()


def main(cwd=None):
    """
    The main() function implements all of the logic that the
    command-line version of onionshare uses.
    """
    strings.load_strings(common)
    print(strings._('version_string').format(common.get_version()))

    # OnionShare CLI in OSX needs to change current working directory (#132)
    if common.get_platform() == 'Darwin':
        if cwd:
            os.chdir(cwd)

    args = _parse_cmdline_args()

    filenames = []
    for f in args.filename:
        filenames.append(os.path.abspath(f.name))
        f.close()

    if args.config:
        args.config.close()
        args.config = args.config.name

    # Debug mode?
    if args.debug:
        common.set_debug(True)
        web.debug_mode()

    settings = Settings(args.config)

    # Start the Onion object
    onion = Onion()
    try:
        onion.connect(settings=False, config=args.config)
    except (BundledTorNotSupported,
            BundledTorTimeout,
            TorErrorAuthError,
            TorErrorAutomatic,
            TorErrorInvalidSetting,
            TorErrorMissingPassword,
            TorErrorProtocolError,
            TorErrorSocketFile,
            TorErrorSocketPort,
            TorErrorUnreadableCookieFile,
            TorTooOld) as e:
        sys.exit(e.args[0])
    except KeyboardInterrupt:
        print("")
        sys.exit()

    # Start the onionshare app
    try:
        app = OnionShare(
            onion,
            args.local_only,
            args.stay_open,
            args.shutdown_timeout)
        app.set_stealth(args.stealth)
        app.start_onion_service()
    except KeyboardInterrupt:
        print("")
        sys.exit()

    # Prepare files to share
    print(strings._("preparing_files"))
    try:
        web.set_file_info(filenames)
        app.cleanup_filenames.append(web.zip_filename)
    except OSError as e:
        print(e.strerror)
        sys.exit(1)

    # Warn about sending large files over Tor
    if web.zip_filesize >= 157286400:  # 150mb
        print('')
        print(strings._("large_filesize"))
        print('')

    # Start OnionShare http service in new thread
    settings.load()
    t = threading.Thread(
        target=web.start,
        args=(app.port, app.stay_open, settings.get('slug')))
    t.daemon = True
    t.start()

    try:  # Trap Ctrl-C
        # Wait for web.generate_slug() to finish running
        time.sleep(0.2)

        # start shutdown timer thread
        if app.shutdown_timeout > 0:
            app.shutdown_timer.start()

        # Save the web slug if we are using a persistent private key
        if settings.get('save_private_key'):
            if not settings.get('slug'):
                settings.set('slug', web.slug)
                settings.save()

        if args.stealth:
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
            if app.shutdown_timeout > 0:
                # if the shutdown timer was set and has run out, stop the server
                if not app.shutdown_timer.is_alive():
                    # If there were no attempts to download the share, or all downloads are done, we can stop
                    if web.download_count == 0 or web.done:
                        print(strings._("close_on_timeout"))
                        web.stop(app.port)
                        break
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
