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
import base64
import hashlib
import inspect
import os
import platform
import random
import socket
import sys
import tempfile
import threading
import time

from .settings import Settings


class Common(object):
    """
    The Common object is shared amongst all parts of OnionShare.
    """
    def __init__(self, debug=False):
        self.debug = debug

        # The platform OnionShare is running on
        self.platform = platform.system()
        if self.platform.endswith('BSD'):
            self.platform = 'BSD'

        # The current version of OnionShare
        with open(self.get_resource_path('version.txt')) as f:
            self.version = f.read().strip()

    def load_settings(self, config=None):
        """
        Loading settings, optionally from a custom config json file.
        """
        self.settings = Settings(self, config)
        self.settings.load()

    def log(self, module, func, msg=None):
        """
        If debug mode is on, log error messages to stdout
        """
        if self.debug:
            timestamp = time.strftime("%b %d %Y %X")

            final_msg = "[{}] {}.{}".format(timestamp, module, func)
            if msg:
                final_msg = '{}: {}'.format(final_msg, msg)
            print(final_msg)

    def get_resource_path(self, filename):
        """
        Returns the absolute path of a resource, regardless of whether OnionShare is installed
        systemwide, and whether regardless of platform
        """
        # On Windows, and in Windows dev mode, switch slashes in incoming filename to backslackes
        if self.platform == 'Windows':
            filename = filename.replace('/', '\\')

        if getattr(sys, 'onionshare_dev_mode', False):
            # Look for resources directory relative to python file
            prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'share')
            if not os.path.exists(prefix):
                # While running tests during stdeb bdist_deb, look 3 directories up for the share folder
                prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(prefix)))), 'share')

        elif self.platform == 'BSD' or self.platform == 'Linux':
            # Assume OnionShare is installed systemwide in Linux, since we're not running in dev mode
            prefix = os.path.join(sys.prefix, 'share/onionshare')

        elif getattr(sys, 'frozen', False):
            # Check if app is "frozen"
            # https://pythonhosted.org/PyInstaller/#run-time-information
            if self.platform == 'Darwin':
                prefix = os.path.join(sys._MEIPASS, 'share')
            elif self.platform == 'Windows':
                prefix = os.path.join(os.path.dirname(sys.executable), 'share')

        return os.path.join(prefix, filename)

    def get_tor_paths(self):
        if self.platform == 'Linux':
            tor_path = '/usr/bin/tor'
            tor_geo_ip_file_path = '/usr/share/tor/geoip'
            tor_geo_ipv6_file_path = '/usr/share/tor/geoip6'
            obfs4proxy_file_path = '/usr/bin/obfs4proxy'
        elif self.platform == 'Windows':
            base_path = os.path.join(os.path.dirname(os.path.dirname(self.get_resource_path(''))), 'tor')
            tor_path               = os.path.join(os.path.join(base_path, 'Tor'), 'tor.exe')
            obfs4proxy_file_path   = os.path.join(os.path.join(base_path, 'Tor'), 'obfs4proxy.exe')
            tor_geo_ip_file_path   = os.path.join(os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip')
            tor_geo_ipv6_file_path = os.path.join(os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip6')
        elif self.platform == 'Darwin':
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(self.get_resource_path(''))))
            tor_path               = os.path.join(base_path, 'Resources', 'Tor', 'tor')
            tor_geo_ip_file_path   = os.path.join(base_path, 'Resources', 'Tor', 'geoip')
            tor_geo_ipv6_file_path = os.path.join(base_path, 'Resources', 'Tor', 'geoip6')
            obfs4proxy_file_path   = os.path.join(base_path, 'Resources', 'Tor', 'obfs4proxy')
        elif self.platform == 'BSD':
            tor_path = '/usr/local/bin/tor'
            tor_geo_ip_file_path = '/usr/local/share/tor/geoip'
            tor_geo_ipv6_file_path = '/usr/local/share/tor/geoip6'
            obfs4proxy_file_path = '/usr/local/bin/obfs4proxy'

        return (tor_path, tor_geo_ip_file_path, tor_geo_ipv6_file_path, obfs4proxy_file_path)

    def build_data_dir(self):
        """
        Returns the path of the OnionShare data directory.
        """
        if self.platform == 'Windows':
            try:
                appdata = os.environ['APPDATA']
                onionshare_data_dir = '{}\\OnionShare'.format(appdata)
            except:
                # If for some reason we don't have the 'APPDATA' environment variable
                # (like running tests in Linux while pretending to be in Windows)
                onionshare_data_dir = os.path.expanduser('~/.config/onionshare')
        elif self.platform == 'Darwin':
            onionshare_data_dir = os.path.expanduser('~/Library/Application Support/OnionShare')
        else:
            onionshare_data_dir = os.path.expanduser('~/.config/onionshare')

        os.makedirs(onionshare_data_dir, 0o700, True)
        return onionshare_data_dir

    def build_slug(self):
        """
        Returns a random string made from two words from the wordlist, such as "deter-trig".
        """
        with open(self.get_resource_path('wordlist.txt')) as f:
            wordlist = f.read().split()

        r = random.SystemRandom()
        return '-'.join(r.choice(wordlist) for _ in range(2))

    def define_css(self):
        """
        This defines all of the stylesheets used in GUI mode, to avoid repeating code.
        This method is only called in GUI mode.
        """
        self.css = {
            # OnionShareGui styles
            'mode_switcher_selected_style': """
                QPushButton {
                    color: #ffffff;
                    background-color: #4e064f;
                    border: 0;
                    border-right: 1px solid #69266b;
                    font-weight: bold;
                    border-radius: 0;
                }""",

            'mode_switcher_unselected_style': """
                QPushButton {
                    color: #ffffff;
                    background-color: #601f61;
                    border: 0;
                    font-weight: normal;
                    border-radius: 0;
                }""",

            'settings_button': """
                QPushButton {
                    background-color: #601f61;
                    border: 0;
                    border-left: 1px solid #69266b;
                    border-radius: 0;
                }""",

            'server_status_indicator_label': """
                QLabel {
                    font-style: italic;
                    color: #666666;
                    padding: 2px;
                }""",

            'status_bar': """
                QStatusBar {
                    font-style: italic;
                    color: #666666;
                }
                QStatusBar::item {
                    border: 0px;
                }""",

            # Common styles between ShareMode and ReceiveMode and their child widgets
            'mode_info_label': """
                QLabel {
                    font-size: 12px;
                    color: #666666;
                }
                """,

            'server_status_url': """
                QLabel {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 10px;
                    border: 1px solid #666666;
                    font-size: 12px;
                }
                """,

            'server_status_url_buttons': """
                QPushButton {
                    color: #3f7fcf;
                }
                """,

            'server_status_button_stopped': """
                QPushButton {
                    background-color: #5fa416;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                }""",

            'server_status_button_working': """
                QPushButton {
                    background-color: #4c8211;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                    font-style: italic;
                }""",

            'server_status_button_started': """
                QPushButton {
                    background-color: #d0011b;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                }""",

            'downloads_uploads_empty': """
                QWidget {
                    background-color: #ffffff;
                    border: 1px solid #999999;
                }
                QWidget QLabel {
                    background-color: none;
                    border: 0px;
                }
                """,

            'downloads_uploads_empty_text': """
                QLabel {
                    color: #999999;
                }""",

            'downloads_uploads_label': """
                QLabel {
                    font-weight: bold;
                    font-size 14px;
                    text-align: center;
                    background-color: none;
                    border: none;
                }""",

            'downloads_uploads_clear': """
                QPushButton {
                    color: #3f7fcf;
                }
                """,

            'download_uploads_indicator': """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 2px;
                    border-radius: 7px;
                    text-align: center;
                }""",

            'downloads_uploads_progress_bar': """
                QProgressBar {
                    border: 1px solid #4e064f;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                    font-size: 14px;
                }
                QProgressBar::chunk {
                    background-color: #4e064f;
                    width: 10px;
                }""",

            # Share mode and child widget styles
            'share_zip_progess_bar': """
                QProgressBar {
                    border: 1px solid #4e064f;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                }
                QProgressBar::chunk {
                    border: 0px;
                    background-color: #4e064f;
                    width: 10px;
                }""",

            'share_filesize_warning': """
                QLabel {
                    padding: 10px 0;
                    font-weight: bold;
                    color: #333333;
                }
                """,

            'share_file_selection_drop_here_label': """
                QLabel {
                    color: #999999;
                }""",

            'share_file_selection_drop_count_label': """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 10px;
                }""",

            'share_file_list_drag_enter': """
                FileList {
                    border: 3px solid #538ad0;
                }
                """,

            'share_file_list_drag_leave': """
                FileList {
                    border: none;
                }
                """,

            'share_file_list_item_size': """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",

            # Receive mode and child widget styles
            'receive_file': """
                QWidget {
                    background-color: #ffffff;
                }
                """,

            'receive_file_size': """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",

            # Settings dialog
            'settings_version': """
                QLabel {
                    color: #666666;
                }""",

            'settings_tor_status': """
                QLabel {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 10px;
                }""",

            'settings_whats_this': """
                QLabel {
                    font-size: 12px;
                }""",

            'settings_connect_to_tor': """
                QLabel {
                    font-style: italic;
                }"""
        }

    @staticmethod
    def random_string(num_bytes, output_len=None):
        """
        Returns a random string with a specified number of bytes.
        """
        b = os.urandom(num_bytes)
        h = hashlib.sha256(b).digest()[:16]
        s = base64.b32encode(h).lower().replace(b'=', b'').decode('utf-8')
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
            return '{:.1f} B'.format(b)
        units = ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')
        u = 0
        b /= thresh
        while b >= thresh:
            b /= thresh
            u += 1
        return '{:.1f} {}'.format(b, units[u])

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
        return ''.join(human_readable)

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
                except OSError as e:
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


class ShutdownTimer(threading.Thread):
    """
    Background thread sleeps t hours and returns.
    """
    def __init__(self, common, time):
        threading.Thread.__init__(self)

        self.common = common

        self.setDaemon(True)
        self.time = time

    def run(self):
        self.common.log('Shutdown Timer', 'Server will shut down after {} seconds'.format(self.time))
        time.sleep(self.time)
        return 1
