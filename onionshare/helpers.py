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
import sys, os, inspect, hashlib, base64, hmac, platform, zipfile, tempfile, math, time


def get_platform():
    """
    Returns the platform OnionShare is running on.
    """
    return platform.system()

def get_onionshare_dir():
    """
    Returns the OnionShare directory.
    """
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def get_pyinstaller_resource_path(filename):
    """
    Returns the path a resource file in a frozen PyInstall app
    """
    # Resource path from frozen PyInstaller app
    # https://pythonhosted.org/PyInstaller/#run-time-information
    p = get_platform()
    if p == 'Darwin':
        return os.path.join(os.path.join(os.path.dirname(sys._MEIPASS), 'Resources'), filename)
    elif p == 'Windows':
        return os.path.join(sys._MEIPASS, filename)

def get_html_path(filename):
    """
    Returns the path of the html files.
    """
    p = get_platform()
    if p == 'Darwin' or p == 'Windows':
        prefix = get_pyinstaller_resource_path('html')
    else:
        prefix = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return os.path.join(prefix, filename)


def get_version():
    """
    Returns the version of OnionShare that is running.
    """
    p = get_platform()
    if p == 'Linux':
        version_filename = os.path.join(sys.prefix, 'share/onionshare/version.txt')
    elif p == 'Darwin' or p == 'Windows':
        version_filename = get_pyinstaller_resource_path('version.txt')
    else:
        return None
    return open(version_filename).read().strip()


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
