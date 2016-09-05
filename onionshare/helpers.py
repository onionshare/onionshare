# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2016 Micah Lee <micah@micahflee.com>

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
import sys, os, inspect, hashlib, base64, platform, zipfile, tempfile, math, time
from random import SystemRandom


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
    if p == 'Linux' and sys.argv and sys.argv[0].startswith('/usr/bin/onionshare'):
        # OnionShare is installed systemwide in Linux
        resources_dir = os.path.join(sys.prefix, 'share/onionshare')
    elif getattr(sys, 'frozen', False): # Check if app is "frozen" with pyinstaller, cx_Freeze
        # https://pythonhosted.org/PyInstaller/#run-time-information
		# http://cx-freeze.readthedocs.io/en/latest/faq.html#using-data-files
		if p == 'Windows':
			# Windows is using cx_Freeze
			resources_dir = os.path.join(os.path.dirname(sys.executable), 'resources')
		else:
			# OS X is using PyInstaller
			resources_dir = sys._MEIPASS
    else:  # Look for resources directory relative to python file
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'resources')

    return os.path.join(resources_dir, filename)


def get_version():
    """
    Returns the version of OnionShare that is running.
    """
    return open(get_resource_path('version.txt')).read().strip()


def constant_time_compare(val1, val2):
    """
    Returns True if the two strings are equal, False otherwise.

    The time taken is independent of the number of characters that match.

    For the sake of simplicity, this function executes in constant time only
    when the two strings have the same length. It short-circuits when they
    have different lengths.

    From: http://www.levigross.com/2014/02/07/constant-time-comparison-functions-in...-python-haskell-clojure-and-java/
    """
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= x ^ y
    return result == 0


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
    wordlist = open(get_resource_path('wordlist.txt')).read().split('\n')
    wordlist.remove('')

    r = SystemRandom()
    return '-'.join(r.choice(wordlist) for x in range(2))


def human_readable_filesize(b):
    """
    Returns filesize in a human readable format.
    """
    thresh = 1024.0
    if b < thresh:
        return '{0:.1f} B'.format(b)
    units = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    u = 0
    b /= thresh
    while b >= thresh:
        b /= thresh
        u += 1
    return '{0:.1f} {1:s}'.format(round(b, 1), units[u])


def format_seconds(seconds):
    """Return a human-readable string of the format 1d2h3m4s"""
    seconds_in_a_minute = 60
    seconds_in_an_hour = seconds_in_a_minute * 60
    seconds_in_a_day = seconds_in_an_hour * 24

    days = math.floor(seconds / seconds_in_a_day)

    hour_seconds = seconds % seconds_in_a_day
    hours = math.floor(hour_seconds / seconds_in_an_hour)

    minute_seconds = hour_seconds % seconds_in_an_hour
    minutes = math.floor(minute_seconds / seconds_in_a_minute)

    remaining_seconds = minute_seconds % seconds_in_a_minute
    seconds = math.ceil(remaining_seconds)

    human_readable = []
    if days > 0:
        human_readable.append("{}d".format(int(days)))
    if hours > 0:
        human_readable.append("{}h".format(int(hours)))
    if minutes > 0:
        human_readable.append("{}m".format(int(minutes)))
    if seconds > 0:
        human_readable.append("{}s".format(int(seconds)))
    return ''.join(human_readable)


def estimated_time_remaining(bytes_downloaded, total_bytes, started):
    now = time.time()
    time_elapsed = now - started  # in seconds
    download_rate = bytes_downloaded / time_elapsed
    remaining_bytes = total_bytes - bytes_downloaded
    eta = remaining_bytes / download_rate
    return format_seconds(eta)


def is_root():
    """
    Returns if user is root.
    """
    return os.geteuid() == 0


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
    def __init__(self, zip_filename=None):
        if zip_filename:
            self.zip_filename = zip_filename
        else:
            self.zip_filename = '{0:s}/onionshare_{1:s}.zip'.format(tempfile.mkdtemp(), random_string(4, 6))

        self.z = zipfile.ZipFile(self.zip_filename, 'w', allowZip64=True)

    def add_file(self, filename):
        """
        Add a file to the zip archive.
        """
        self.z.write(filename, os.path.basename(filename), zipfile.ZIP_DEFLATED)

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

    def close(self):
        """
        Close the zip archive.
        """
        self.z.close()
