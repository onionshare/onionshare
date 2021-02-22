# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
from datetime import datetime
from datetime import timedelta

from .common import Common, CannotFindTor
from .web import Web
from .onion import *
from .onionshare import OnionShare
from .mode_settings import ModeSettings


def build_url(mode_settings, app, web):
    # Build the URL
    if mode_settings.get("general", "public"):
        return f"http://{app.onion_host}"
    else:
        return f"http://onionshare:{web.password}@{app.onion_host}"


def main(cwd=None):
    """
    The main() function implements all of the logic that the command-line version of
    onionshare uses.
    """
    common = Common()

    # Display OnionShare banner
    print(f"OnionShare {common.version} | https://onionshare.org/")
    reset = "\033[0m"
    purple = "\33[95m"
    print(purple)
    print("                     @@@@@@@@@                      ")
    print("                @@@@@@@@@@@@@@@@@@@                 ")
    print("             @@@@@@@@@@@@@@@@@@@@@@@@@              ")
    print("           @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            ")
    print(
        "             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@           ___        _               "
    )
    print(
        "               @@@@@@         @@@@@@@@@@@@@         / _ \\      (_)              "
    )
    print(
        "         @@@@    @               @@@@@@@@@@@       | | | |_ __  _  ___  _ __    "
    )
    print(
        "       @@@@@@@@                   @@@@@@@@@@       | | | | '_ \\| |/ _ \\| '_ \\   "
    )
    print(
        "     @@@@@@@@@@@@                  @@@@@@@@@@      \\ \\_/ / | | | | (_) | | | |  "
    )
    print(
        "   @@@@@@@@@@@@@@@@                 @@@@@@@@@       \\___/|_| |_|_|\\___/|_| |_|  "
    )
    print(
        "      @@@@@@@@@                 @@@@@@@@@@@@@@@@    _____ _                     "
    )
    print(
        "      @@@@@@@@@@                  @@@@@@@@@@@@     /  ___| |                    "
    )
    print(
        "       @@@@@@@@@@                   @@@@@@@@       \\ `--.| |__   __ _ _ __ ___ "
    )
    print(
        "       @@@@@@@@@@@               @    @@@@          `--. \\ '_ \\ / _` | '__/ _ \\"
    )
    print(
        "        @@@@@@@@@@@@@         @@@@@@               /\\__/ / | | | (_| | | |  __/"
    )
    print(
        "         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@             \\____/|_| |_|\\__,_|_|  \\___|"
    )
    print("           @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            ")
    print("             @@@@@@@@@@@@@@@@@@@@@@@@@              ")
    print("                @@@@@@@@@@@@@@@@@@@                 ")
    print("                     @@@@@@@@@                      ")
    print(reset)

    # OnionShare CLI in OSX needs to change current working directory (#132)
    if common.platform == "Darwin":
        if cwd:
            os.chdir(cwd)

    # Parse arguments
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=28)
    )
    # Select modes
    parser.add_argument(
        "--receive", action="store_true", dest="receive", help="Receive files"
    )
    parser.add_argument(
        "--website", action="store_true", dest="website", help="Publish website"
    )
    parser.add_argument(
        "--chat", action="store_true", dest="chat", help="Start chat server"
    )
    # Tor connection-related args
    parser.add_argument(
        "--local-only",
        action="store_true",
        dest="local_only",
        default=False,
        help="Don't use Tor (only for development)",
    )
    parser.add_argument(
        "--connect-timeout",
        metavar="SECONDS",
        dest="connect_timeout",
        default=120,
        help="Give up connecting to Tor after a given amount of seconds (default: 120)",
    )
    parser.add_argument(
        "--config",
        metavar="FILENAME",
        default=None,
        help="Filename of custom global settings",
    )
    # Persistent file
    parser.add_argument(
        "--persistent",
        metavar="FILENAME",
        default=None,
        help="Filename of persistent session",
    )
    # General args
    parser.add_argument(
        "--public",
        action="store_true",
        dest="public",
        default=False,
        help="Don't use a password",
    )
    parser.add_argument(
        "--auto-start-timer",
        metavar="SECONDS",
        dest="autostart_timer",
        default=0,
        help="Start onion service at scheduled time (N seconds from now)",
    )
    parser.add_argument(
        "--auto-stop-timer",
        metavar="SECONDS",
        dest="autostop_timer",
        default=0,
        help="Stop onion service at schedule time (N seconds from now)",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        dest="legacy",
        default=False,
        help="Use legacy address (v2 onion service, not recommended)",
    )
    parser.add_argument(
        "--client-auth",
        action="store_true",
        dest="client_auth",
        default=False,
        help="Use client authorization (requires --legacy)",
    )
    # Share args
    parser.add_argument(
        "--no-autostop-sharing",
        action="store_true",
        dest="no_autostop_sharing",
        default=False,
        help="Share files: Continue sharing after files have been sent (default is to stop sharing)",
    )
    # Receive args
    parser.add_argument(
        "--data-dir",
        metavar="data_dir",
        default=None,
        help="Receive files: Save files received to this directory",
    )
    # Website args
    parser.add_argument(
        "--disable_csp",
        action="store_true",
        dest="disable_csp",
        default=False,
        help="Publish website: Disable Content Security Policy header (allows your website to use third-party resources)",
    )
    # Other
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Log OnionShare errors to stdout, and web errors to disk",
    )
    parser.add_argument(
        "filename",
        metavar="filename",
        nargs="*",
        help="List of files or folders to share",
    )
    args = parser.parse_args()

    filenames = args.filename
    for i in range(len(filenames)):
        filenames[i] = os.path.abspath(filenames[i])

    receive = bool(args.receive)
    website = bool(args.website)
    chat = bool(args.chat)
    local_only = bool(args.local_only)
    connect_timeout = int(args.connect_timeout)
    config_filename = args.config
    persistent_filename = args.persistent
    public = bool(args.public)
    autostart_timer = int(args.autostart_timer)
    autostop_timer = int(args.autostop_timer)
    legacy = bool(args.legacy)
    client_auth = bool(args.client_auth)
    autostop_sharing = not bool(args.no_autostop_sharing)
    data_dir = args.data_dir
    disable_csp = bool(args.disable_csp)
    verbose = bool(args.verbose)

    if receive:
        mode = "receive"
    elif website:
        mode = "website"
    elif chat:
        mode = "chat"
    else:
        mode = "share"

    # Verbose mode?
    common.verbose = verbose

    # client_auth can only be set if legacy is also set
    if client_auth and not legacy:
        print(
            "Client authentication (--client-auth) is only supported with with legacy onion services (--legacy)"
        )
        sys.exit()

    # Re-load settings, if a custom config was passed in
    if config_filename:
        common.load_settings(config_filename)
    else:
        common.load_settings()

    # Mode settings
    if persistent_filename:
        mode_settings = ModeSettings(common, persistent_filename)
        mode_settings.set("persistent", "enabled", True)
        mode_settings.set("persistent", "mode", mode)
    else:
        mode_settings = ModeSettings(common)

    if mode_settings.just_created:
        # This means the mode settings were just created, not loaded from disk
        mode_settings.set("general", "public", public)
        mode_settings.set("general", "autostart_timer", autostart_timer)
        mode_settings.set("general", "autostop_timer", autostop_timer)
        mode_settings.set("general", "legacy", legacy)
        mode_settings.set("general", "client_auth", client_auth)
        if mode == "share":
            mode_settings.set("share", "autostop_sharing", autostop_sharing)
        if mode == "receive":
            if data_dir:
                mode_settings.set("receive", "data_dir", data_dir)
        if mode == "website":
            mode_settings.set("website", "disable_csp", disable_csp)
    else:
        # See what the persistent mode was
        mode = mode_settings.get("persistent", "mode")

    # In share and website mode, you must supply a list of filenames
    if mode == "share" or mode == "website":
        # Unless you passed in a persistent filename, in which case get the filenames from
        # the mode settings
        if (
            persistent_filename
            and not mode_settings.just_created
            and len(filenames) != 0
        ):
            filenames = mode_settings.get(mode, "filenames")

        else:
            # Make sure filenames given if not using receiver mode
            if len(filenames) == 0:
                if persistent_filename:
                    mode_settings.delete()

                parser.print_help()
                sys.exit()

            # Validate filenames
            valid = True
            for filename in filenames:
                if not os.path.isfile(filename) and not os.path.isdir(filename):
                    print(f"{filename} is not a valid file.")
                    valid = False
                if not os.access(filename, os.R_OK):
                    print(f"{filename} is not a readable file.")
                    valid = False
            if not valid:
                sys.exit()

        # Save the filenames in persistent file
        if persistent_filename:
            mode_settings.set(mode, "filenames", filenames)

    # Create the Web object
    web = Web(common, False, mode_settings, mode)

    # Start the Onion object
    try:
        onion = Onion(common, use_tmp_dir=True)
    except CannotFindTor:
        print("You must install tor to use OnionShare from the command line")
        if common.platform == "Darwin":
            print("In macOS, you can do this with Homebrew (https://brew.sh):")
            print("  brew install tor")
        sys.exit()

    try:
        onion.connect(
            custom_settings=False,
            config=config_filename,
            connect_timeout=connect_timeout,
            local_only=local_only,
        )
    except KeyboardInterrupt:
        print("")
        sys.exit()
    except Exception as e:
        sys.exit()

    # Start the onionshare app
    try:
        common.settings.load()
        if not mode_settings.get("general", "public"):
            web.generate_password(mode_settings.get("onion", "password"))
        else:
            web.password = None
        app = OnionShare(common, onion, local_only, autostop_timer)
        app.choose_port()

        # Delay the startup if a startup timer was set
        if autostart_timer > 0:
            # Can't set a schedule that is later than the auto-stop timer
            if autostop_timer > 0 and autostop_timer < autostart_timer:
                print(
                    "The auto-stop time can't be the same or earlier than the auto-start time. Please update it to start sharing."
                )
                sys.exit()

            app.start_onion_service(mode, mode_settings, False, True)
            url = build_url(mode_settings, app, web)
            schedule = datetime.now() + timedelta(seconds=autostart_timer)
            if mode == "receive":
                print(
                    f"Files sent to you appear in this folder: {mode_settings.get('receive', 'data_dir')}"
                )
                print("")
                print(
                    "Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing."
                )
                print("")
                if mode_settings.get("general", "client_auth"):
                    print(
                        f"Give this address and HidServAuth lineto your sender, and tell them it won't be accessible until: {schedule.strftime('%I:%M:%S%p, %b %d, %y')}"
                    )
                    print(app.auth_string)
                else:
                    print(
                        f"Give this address to your sender, and tell them it won't be accessible until: {schedule.strftime('%I:%M:%S%p, %b %d, %y')}"
                    )
            else:
                if mode_settings.get("general", "client_auth"):
                    print(
                        f"Give this address and HidServAuth line to your recipient, and tell them it won't be accessible until: {schedule.strftime('%I:%M:%S%p, %b %d, %y')}"
                    )
                    print(app.auth_string)
                else:
                    print(
                        f"Give this address to your recipient, and tell them it won't be accessible until: {schedule.strftime('%I:%M:%S%p, %b %d, %y')}"
                    )
            print(url)
            print("")
            print("Waiting for the scheduled time before starting...")
            app.onion.cleanup(False)
            time.sleep(autostart_timer)
            app.start_onion_service(mode, mode_settings)
        else:
            app.start_onion_service(mode, mode_settings)
    except KeyboardInterrupt:
        print("")
        sys.exit()
    except (TorTooOld, TorErrorProtocolError) as e:
        print("")
        print(e.args[0])
        sys.exit()

    if mode == "website":
        # Prepare files to share
        try:
            web.website_mode.set_file_info(filenames)
        except OSError as e:
            print(e.strerror)
            sys.exit(1)

    if mode == "share":
        # Prepare files to share
        print("Compressing files.")
        try:
            web.share_mode.set_file_info(filenames)
            app.cleanup_filenames += web.share_mode.cleanup_filenames
        except OSError as e:
            print(e.strerror)
            sys.exit(1)

        # Warn about sending large files over Tor
        if web.share_mode.download_filesize >= 157286400:  # 150mb
            print("")
            print("Warning: Sending a large share could take hours")
            print("")

    # Start OnionShare http service in new thread
    t = threading.Thread(target=web.start, args=(app.port,))
    t.daemon = True
    t.start()

    try:  # Trap Ctrl-C
        # Wait for web.generate_password() to finish running
        time.sleep(0.2)

        # start auto-stop timer thread
        if app.autostop_timer > 0:
            app.autostop_timer_thread.start()

        # Save the web password if we are using a persistent private key
        if mode_settings.get("persistent", "enabled"):
            if not mode_settings.get("onion", "password"):
                mode_settings.set("onion", "password", web.password)
                # mode_settings.save()

        # Build the URL
        url = build_url(mode_settings, app, web)

        print("")
        if autostart_timer > 0:
            print("Server started")
        else:
            if mode == "receive":
                print(
                    f"Files sent to you appear in this folder: {mode_settings.get('receive', 'data_dir')}"
                )
                print("")
                print(
                    "Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing."
                )
                print("")

                if mode_settings.get("general", "client_auth"):
                    print("Give this address and HidServAuth to the sender:")
                    print(url)
                    print(app.auth_string)
                else:
                    print("Give this address to the sender:")
                    print(url)
            else:
                if mode_settings.get("general", "client_auth"):
                    print("Give this address and HidServAuth line to the recipient:")
                    print(url)
                    print(app.auth_string)
                else:
                    print("Give this address to the recipient:")
                    print(url)
        print("")
        print("Press Ctrl+C to stop the server")

        # Wait for app to close
        while t.is_alive():
            if app.autostop_timer > 0:
                # if the auto-stop timer was set and has run out, stop the server
                if not app.autostop_timer_thread.is_alive():
                    if mode == "share" or (mode == "website"):
                        # If there were no attempts to download the share, or all downloads are done, we can stop
                        if web.share_mode.cur_history_id == 0 or web.done:
                            print("Stopped because auto-stop timer ran out")
                            web.stop(app.port)
                            break
                    if mode == "receive":
                        if (
                            web.receive_mode.cur_history_id == 0
                            or not web.receive_mode.uploads_in_progress
                        ):
                            print("Stopped because auto-stop timer ran out")
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


if __name__ == "__main__":
    main()
