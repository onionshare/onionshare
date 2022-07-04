# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
import base64
import hashlib
import os
import platform
import random
import requests
import socket
import sys
import threading
import time
import shutil
import re
from pkg_resources import resource_filename

import colorama
from colorama import Fore, Back, Style

from .settings import Settings


class CannotFindTor(Exception):
    """
    OnionShare can't find a tor binary
    """


class Common:
    """
    The Common object is shared amongst all parts of OnionShare.
    """

    def __init__(self, verbose=False):
        self.verbose = verbose

        colorama.init(autoreset=True)

        # The platform OnionShare is running on
        self.platform = platform.system()
        if self.platform.endswith("BSD") or self.platform == "DragonFly":
            self.platform = "BSD"

        # The current version of OnionShare
        with open(self.get_resource_path("version.txt")) as f:
            self.version = f.read().strip()

    def display_banner(self):
        """
        Raw ASCII art example:
        ╭───────────────────────────────────────────╮
        │    *            ▄▄█████▄▄            *    │
        │               ▄████▀▀▀████▄     *         │
        │              ▀▀█▀       ▀██▄              │
        │      *      ▄█▄          ▀██▄             │
        │           ▄█████▄         ███        -+-  │
        │             ███         ▀█████▀           │
        │             ▀██▄          ▀█▀             │
        │         *    ▀██▄       ▄█▄▄     *        │
        │ *             ▀████▄▄▄████▀               │
        │                 ▀▀█████▀▀                 │
        │             -+-                     *     │
        │   ▄▀▄               ▄▀▀ █                 │
        │   █ █     ▀         ▀▄  █                 │
        │   █ █ █▀▄ █ ▄▀▄ █▀▄  ▀▄ █▀▄ ▄▀▄ █▄▀ ▄█▄   │
        │   ▀▄▀ █ █ █ ▀▄▀ █ █ ▄▄▀ █ █ ▀▄█ █   ▀▄▄   │
        │                                           │
        │                  v2.3.1                   │
        │                                           │
        │          https://onionshare.org/          │
        ╰───────────────────────────────────────────╯
        """

        try:
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "╭───────────────────────────────────────────╮"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.LIGHTMAGENTA_EX
                + "    *            "
                + Fore.WHITE
                + "▄▄█████▄▄"
                + Fore.LIGHTMAGENTA_EX
                + "            *    "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "               ▄████▀▀▀████▄"
                + Fore.LIGHTMAGENTA_EX
                + "     *         "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "              ▀▀█▀       ▀██▄              "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.LIGHTMAGENTA_EX
                + "      *      "
                + Fore.WHITE
                + "▄█▄          ▀██▄             "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "           ▄█████▄         ███"
                + Fore.LIGHTMAGENTA_EX
                + "        -+-  "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "             ███         ▀█████▀           "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "             ▀██▄          ▀█▀             "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.LIGHTMAGENTA_EX
                + "         *    "
                + Fore.WHITE
                + "▀██▄       ▄█▄▄"
                + Fore.LIGHTMAGENTA_EX
                + "     *        "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.LIGHTMAGENTA_EX
                + " *             "
                + Fore.WHITE
                + "▀████▄▄▄████▀               "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "                 ▀▀█████▀▀                 "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.LIGHTMAGENTA_EX
                + "             -+-                     *     "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "   ▄▀▄               ▄▀▀ █                 "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "   █ █     ▀         ▀▄  █                 "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "   █ █ █▀▄ █ ▄▀▄ █▀▄  ▀▄ █▀▄ ▄▀▄ █▄▀ ▄█▄   "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "   ▀▄▀ █ █ █ ▀▄▀ █ █ ▄▄▀ █ █ ▀▄█ █   ▀▄▄   "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│                                           │"
            )
            left_spaces = (43 - len(self.version) - 1) // 2
            right_spaces = left_spaces
            if left_spaces + len(self.version) + 1 + right_spaces < 43:
                right_spaces += 1
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + f"{' '*left_spaces}v{self.version}{' '*right_spaces}"
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│                                           │"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "│"
                + Fore.WHITE
                + "          https://onionshare.org/          "
                + Fore.WHITE
                + "│"
            )
            print(
                Back.MAGENTA
                + Fore.WHITE
                + "╰───────────────────────────────────────────╯"
            )
            print()
        except:
            # If anything fails, print a boring banner
            print(f"OnionShare v{self.version}")
            print("https://onionshare.org/")
            print()

    def load_settings(self, config=None):
        """
        Loading settings, optionally from a custom config json file.
        """
        self.settings = Settings(self, config)
        self.settings.load()

    def log(self, module, func, msg=None):
        """
        If verbose mode is on, log error messages to stdout
        """
        if self.verbose:
            timestamp = time.strftime("%b %d %Y %X")
            final_msg = f"{Fore.LIGHTBLACK_EX + Style.DIM}[{timestamp}]{Style.RESET_ALL} {Fore.WHITE + Style.DIM}{module}.{func}{Style.RESET_ALL}"
            if msg:
                final_msg = (
                    f"{final_msg}{Fore.WHITE + Style.DIM}: {msg}{Style.RESET_ALL}"
                )
            print(final_msg)

    def get_resource_path(self, filename):
        """
        Returns the absolute path of a resource
        """
        path = resource_filename("onionshare_cli", os.path.join("resources", filename))
        self.log("Common", "get_resource_path", f"filename={filename}, path={path}")
        return path

    def get_tor_paths(self):
        if self.platform == "Linux":
            tor_path = shutil.which("tor")
            if not tor_path:
                raise CannotFindTor()
            obfs4proxy_file_path = shutil.which("obfs4proxy")
            snowflake_file_path = shutil.which("snowflake-client")
            meek_client_file_path = shutil.which("meek-client")
            prefix = os.path.dirname(os.path.dirname(tor_path))
            tor_geo_ip_file_path = os.path.join(prefix, "share/tor/geoip")
            tor_geo_ipv6_file_path = os.path.join(prefix, "share/tor/geoip6")
        elif self.platform == "Windows":
            # In Windows, the Tor binaries are in the onionshare package, not the onionshare_cli package
            base_path = self.get_resource_path("tor")
            base_path = base_path.replace("onionshare_cli", "onionshare")
            tor_path = os.path.join(base_path, "tor.exe")

            # If tor.exe isn't there, mayber we're running from the source tree
            if not os.path.exists(tor_path):
                self.log(
                    "Common", "get_tor_paths", f"Cannot find tor.exe at {tor_path}"
                )
                base_path = os.path.join(os.getcwd(), "onionshare", "resources", "tor")

                tor_path = os.path.join(base_path, "tor.exe")
                if not os.path.exists(tor_path):
                    self.log(
                        "Common", "get_tor_paths", f"Cannot find tor.exe at {tor_path}"
                    )
                    raise CannotFindTor()

            obfs4proxy_file_path = os.path.join(base_path, "obfs4proxy.exe")
            snowflake_file_path = os.path.join(base_path, "snowflake-client.exe")
            meek_client_file_path = os.path.join(base_path, "meek-client.exe")
            tor_geo_ip_file_path = os.path.join(base_path, "geoip")
            tor_geo_ipv6_file_path = os.path.join(base_path, "geoip6")

        elif self.platform == "Darwin":
            # Let's see if we have tor binaries in the onionshare GUI package
            base_path = self.get_resource_path("tor")
            base_path = base_path.replace("onionshare_cli", "onionshare")
            tor_path = os.path.join(base_path, "tor")
            if os.path.exists(tor_path):
                obfs4proxy_file_path = os.path.join(base_path, "obfs4proxy")
                snowflake_file_path = os.path.join(base_path, "snowflake-client")
                meek_client_file_path = os.path.join(base_path, "meek-client")
                tor_geo_ip_file_path = os.path.join(base_path, "geoip")
                tor_geo_ipv6_file_path = os.path.join(base_path, "geoip6")
            else:
                # Fallback to looking in the path
                tor_path = shutil.which("tor")
                if not os.path.exists(tor_path):
                    raise CannotFindTor()

                obfs4proxy_file_path = shutil.which("obfs4proxy")
                snowflake_file_path = shutil.which("snowflake-client")
                meek_client_file_path = shutil.which("meek-client")
                prefix = os.path.dirname(os.path.dirname(tor_path))
                tor_geo_ip_file_path = os.path.join(prefix, "share/tor/geoip")
                tor_geo_ipv6_file_path = os.path.join(prefix, "share/tor/geoip6")

        elif self.platform == "BSD":
            tor_path = "/usr/local/bin/tor"
            tor_geo_ip_file_path = "/usr/local/share/tor/geoip"
            tor_geo_ipv6_file_path = "/usr/local/share/tor/geoip6"
            obfs4proxy_file_path = "/usr/local/bin/obfs4proxy"
            snowflake_file_path = "/usr/local/bin/snowflake-client"
            meek_client_file_path = "/usr/local/bin/meek-client"

        return (
            tor_path,
            tor_geo_ip_file_path,
            tor_geo_ipv6_file_path,
            obfs4proxy_file_path,
            snowflake_file_path,
            meek_client_file_path,
        )

    def build_data_dir(self):
        """
        Returns the path of the OnionShare data directory.
        """
        if self.platform == "Windows":
            try:
                appdata = os.environ["APPDATA"]
                onionshare_data_dir = f"{appdata}\\OnionShare"
            except Exception:
                # If for some reason we don't have the 'APPDATA' environment variable
                # (like running tests in Linux while pretending to be in Windows)
                try:
                    xdg_config_home = os.environ["XDG_CONFIG_HOME"]
                    onionshare_data_dir = f"{xdg_config_home}/onionshare"
                except Exception:
                    onionshare_data_dir = os.path.expanduser("~/.config/onionshare")
        elif self.platform == "Darwin":
            onionshare_data_dir = os.path.expanduser(
                "~/Library/Application Support/OnionShare"
            )
        else:
            try:
                xdg_config_home = os.environ["XDG_CONFIG_HOME"]
                onionshare_data_dir = f"{xdg_config_home}/onionshare"
            except Exception:
                onionshare_data_dir = os.path.expanduser("~/.config/onionshare")

        # Modify the data dir if running tests
        if getattr(sys, "onionshare_test_mode", False):
            onionshare_data_dir += "-testdata"

        os.makedirs(onionshare_data_dir, 0o700, True)
        return onionshare_data_dir

    def build_tmp_dir(self):
        """
        Returns path to a folder that can hold temporary files
        """
        tmp_dir = os.path.join(self.build_data_dir(), "tmp")
        os.makedirs(tmp_dir, 0o700, True)
        return tmp_dir

    def build_persistent_dir(self):
        """
        Returns the path to the folder that holds persistent files
        """
        persistent_dir = os.path.join(self.build_data_dir(), "persistent")
        os.makedirs(persistent_dir, 0o700, True)
        return persistent_dir

    def build_tor_dir(self):
        """
        Returns path to the tor data directory
        """
        tor_dir = os.path.join(self.build_data_dir(), "tor_data")
        os.makedirs(tor_dir, 0o700, True)
        return tor_dir

    def build_password(self, word_count=2):
        """
        Returns a random string made of words from the wordlist, such as "deter-trig".
        """
        with open(self.get_resource_path("wordlist.txt")) as f:
            wordlist = f.read().split()

        r = random.SystemRandom()
        return "-".join(r.choice(wordlist) for _ in range(word_count))

    def build_username(self, word_count=2):
        """
        Returns a random string made of words from the wordlist, such as "deter-trig".
        """
        with open(self.get_resource_path("wordlist.txt")) as f:
            wordlist = f.read().split()

        r = random.SystemRandom()
        return "-".join(r.choice(wordlist) for _ in range(word_count))

    def check_bridges_valid(self, bridges):
        """
        Does a regex check against a supplied list of bridges, to make sure they
        are valid strings depending on the bridge type.
        """
        valid_bridges = []
        self.log("Common", "check_bridges_valid", "Checking bridge syntax")
        for bridge in bridges:
            if bridge != "":
                # Check the syntax of the custom bridge to make sure it looks legitimate
                ipv4_pattern = re.compile(
                    "(obfs4\s+)?(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):([0-9]+)(\s+)([A-Z0-9]+)(.+)$"
                )
                ipv6_pattern = re.compile(
                    "(obfs4\s+)?\[(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\]:[0-9]+\s+[A-Z0-9]+(.+)$"
                )
                meek_lite_pattern = re.compile(
                    "(meek_lite)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)(\s)+url=(.+)(\s)+front=(.+)"
                )
                snowflake_pattern = re.compile(
                    "(snowflake)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)"
                )
                if (
                    ipv4_pattern.match(bridge)
                    or ipv6_pattern.match(bridge)
                    or meek_lite_pattern.match(bridge)
                    or snowflake_pattern.match(bridge)
                ):
                    valid_bridges.append(bridge)
        if valid_bridges:
            return valid_bridges
        else:
            return False

    def is_flatpak(self):
        """
        Returns True if OnionShare is running in a Flatpak sandbox
        """
        return os.environ.get("FLATPAK_ID") == "org.onionshare.OnionShare"

    def is_snapcraft(self):
        """
        Returns True if OnionShare is running in a Snapcraft sandbox
        """
        return os.environ.get("SNAP_INSTANCE_NAME") == "onionshare"

    @staticmethod
    def random_string(num_bytes, output_len=None):
        """
        Returns a random string with a specified number of bytes.
        """
        b = os.urandom(num_bytes)
        h = hashlib.sha256(b).digest()[:16]
        s = base64.b32encode(h).lower().replace(b"=", b"").decode("utf-8")
        if not output_len:
            return s
        return s[:output_len]

    @staticmethod
    def human_readable_filesize(b):
        """
        Returns filesize in a human readable format.
        """
        thresh = 1024.0
        if b < thresh:
            return "{:.1f} B".format(b)
        units = ("KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
        u = 0
        b /= thresh
        while b >= thresh:
            b /= thresh
            u += 1
        return "{:.1f} {}".format(b, units[u])

    @staticmethod
    def format_seconds(seconds):
        """Return a human-readable string of the format 1d2h3m4s"""
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        human_readable = []
        if days:
            human_readable.append("{:.0f}d".format(days))
        if hours:
            human_readable.append("{:.0f}h".format(hours))
        if minutes:
            human_readable.append("{:.0f}m".format(minutes))
        if seconds or not human_readable:
            human_readable.append("{:.0f}s".format(seconds))
        return "".join(human_readable)

    @staticmethod
    def estimated_time_remaining(bytes_downloaded, total_bytes, started):
        now = time.time()
        time_elapsed = now - started  # in seconds
        download_rate = bytes_downloaded / time_elapsed
        remaining_bytes = total_bytes - bytes_downloaded
        eta = remaining_bytes / download_rate
        return Common.format_seconds(eta)

    @staticmethod
    def get_available_port(min_port, max_port):
        """
        Find a random available port within the given range.
        """
        with socket.socket() as tmpsock:
            while True:
                try:
                    tmpsock.bind(("127.0.0.1", random.randint(min_port, max_port)))
                    break
                except OSError:
                    pass
            _, port = tmpsock.getsockname()
        return port

    @staticmethod
    def dir_size(start_path):
        """
        Calculates the total size, in bytes, of all of the files in a directory.
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size


class AutoStopTimer(threading.Thread):
    """
    Background thread sleeps t hours and returns.
    """

    def __init__(self, common, time):
        threading.Thread.__init__(self)

        self.common = common

        self.setDaemon(True)
        self.time = time

    def run(self):
        self.common.log(
            "AutoStopTimer", f"Server will shut down after {self.time} seconds"
        )
        time.sleep(self.time)
        return 1
