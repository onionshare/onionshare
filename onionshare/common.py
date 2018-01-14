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
import zipfile

debug = False


def log(module, func, msg=None):
    """
    If debug mode is on, log error messages to stdout
    """
    global debug
    if debug:
        timestamp = time.strftime("%b %d %Y %X")

        final_msg = "[{}] {}.{}".format(timestamp, module, func)
        if msg:
            final_msg = '{}: {}'.format(final_msg, msg)
        print(final_msg)


def set_debug(new_debug):
    global debug
    debug = new_debug


def get_platform():
    """
    Returns the platform OnionShare is running on.
    """
    return platform.system()


def get_resource_path(filename):
    """
    Returns the absolute path of a resource, regardless of whether OnionShare is installed
    systemwide, and whether regardless of platform
    """
    p = get_platform()

    if getattr(sys, 'onionshare_dev_mode', False):
        # Look for resources directory relative to python file
        prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'share')
        if not os.path.exists(prefix):
            # While running tests during stdeb bdist_deb, look 3 directories up for the share folder
            prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(prefix)))), 'share')

    elif p == 'Linux':
        # Assume OnionShare is installed systemwide in Linux, since we're not running in dev mode
        prefix = os.path.join(sys.prefix, 'share/onionshare')

    elif getattr(sys, 'frozen', False):
        # Check if app is "frozen"
        # https://pythonhosted.org/PyInstaller/#run-time-information
        if p == 'Darwin':
            prefix = os.path.join(sys._MEIPASS, 'share')
        elif p == 'Windows':
            prefix = os.path.join(os.path.dirname(sys.executable), 'share')

    return os.path.join(prefix, filename)


def get_tor_paths():
    p = get_platform()
    if p == 'Linux':
        tor_path = '/usr/bin/tor'
        tor_geo_ip_file_path = '/usr/share/tor/geoip'
        tor_geo_ipv6_file_path = '/usr/share/tor/geoip6'
    elif p == 'Windows':
        base_path = os.path.join(os.path.dirname(os.path.dirname(get_resource_path(''))), 'tor')
        tor_path               = os.path.join(os.path.join(base_path, 'Tor'), "tor.exe")
        tor_geo_ip_file_path   = os.path.join(os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip')
        tor_geo_ipv6_file_path = os.path.join(os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip6')
    elif p == 'Darwin':
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(get_resource_path(''))))
        tor_path               = os.path.join(base_path, 'Resources', 'Tor', 'tor')
        tor_geo_ip_file_path   = os.path.join(base_path, 'Resources', 'Tor', 'geoip')
        tor_geo_ipv6_file_path = os.path.join(base_path, 'Resources', 'Tor', 'geoip6')
    elif p == 'OpenBSD' or p == 'FreeBSD':
        tor_path = '/usr/local/bin/tor'
        tor_geo_ip_file_path = '/usr/local/share/tor/geoip'
        tor_geo_ipv6_file_path = '/usr/local/share/tor/geoip6'

    return (tor_path, tor_geo_ip_file_path, tor_geo_ipv6_file_path)


def get_version():
    """
    Returns the version of OnionShare that is running.
    """
    with open(get_resource_path('version.txt')) as f:
        version = f.read().strip()
        return version


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


def build_slug():
    """
    Returns a random string made from two words from the wordlist, such as "deter-trig".
    """
    with open(get_resource_path('wordlist.txt')) as f:
        wordlist = f.read().split()

    r = random.SystemRandom()
    return '-'.join(r.choice(wordlist) for _ in range(2))


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


def estimated_time_remaining(bytes_downloaded, total_bytes, started):
    now = time.time()
    time_elapsed = now - started  # in seconds
    download_rate = bytes_downloaded / time_elapsed
    remaining_bytes = total_bytes - bytes_downloaded
    eta = remaining_bytes / download_rate
    return format_seconds(eta)


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
                raise OSError(e)
        _, port = tmpsock.getsockname()
    return port


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


class ZipWriter(object):
    """
    ZipWriter accepts files and directories and compresses them into a zip file
    with. If a zip_filename is not passed in, it will use the default onionshare
    filename.
    """
    def __init__(self, zip_filename=None, processed_size_callback=None, tmpdir=None):
        if zip_filename:
            self.zip_filename = zip_filename
        else:
            self.zip_filename = '{0:s}/onionshare_{1:s}.zip'.format(tempfile.mkdtemp(dir=tmpdir), random_string(4, 6))

        self.z = zipfile.ZipFile(self.zip_filename, 'w', allowZip64=True)
        self.processed_size_callback = processed_size_callback
        if self.processed_size_callback is None:
            self.processed_size_callback = lambda _: None
        self._size = 0
        self.processed_size_callback(self._size)

    def add_file(self, filename):
        """
        Add a file to the zip archive.
        """
        self.z.write(filename, os.path.basename(filename), zipfile.ZIP_DEFLATED)
        self._size += os.path.getsize(filename)
        self.processed_size_callback(self._size)

    def add_dir(self, filename):
        """
        Add a directory, and all of its children, to the zip archive.
        """
        dir_to_strip = os.path.dirname(filename.rstrip('/'))+'/'
        for dirpath, dirnames, filenames in os.walk(filename):
            for f in filenames:
                full_filename = os.path.join(dirpath, f)
                if not os.path.islink(full_filename):
                    arc_filename = full_filename[len(dir_to_strip):]
                    self.z.write(full_filename, arc_filename, zipfile.ZIP_DEFLATED)
                    self._size += os.path.getsize(full_filename)
                    self.processed_size_callback(self._size)

    def close(self):
        """
        Close the zip archive.
        """
        self.z.close()


class close_after_seconds(threading.Thread):
    """
    Background thread sleeps t hours and returns.
    """
    def __init__(self, time):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.time = time

    def run(self):
        log('Shutdown Timer', 'Server will shut down after {} seconds'.format(self.time))
        time.sleep(self.time)
        return 1
