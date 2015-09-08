# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2015 Micah Lee <micah@micahflee.com>

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
import os, inspect, hashlib, base64, hmac, platform, zipfile, tempfile
from itertools import izip

# hack to make unicode filenames work (#141)
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def get_platform():
    return platform.system()

if get_platform() == 'Darwin':
    # this is hacky, but it ultimate ends up returning the absolute path to
    # OnionShare.app/Contents/Resources, based on the location of helpers.py
    helpers_path = os.path.realpath(os.path.abspath(inspect.getfile(inspect.currentframe())))
    osx_resources_dir = os.path.dirname(os.path.dirname(helpers_path))
else:
    osx_resources_dir = None

def get_onionshare_dir():
    if get_platform() == 'Darwin':
        onionshare_dir = os.path.dirname(__file__)
    else:
        onionshare_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return onionshare_dir

def get_html_path(filename):
    p = platform.system()
    if p == 'Darwin':
        prefix = os.path.join(osx_resources_dir, 'html')
    else:
        prefix = get_onionshare_dir()
    return os.path.join(prefix, filename)


def constant_time_compare(val1, val2):
    _builtin_constant_time_compare = getattr(hmac, 'compare_digest', None)
    if _builtin_constant_time_compare is not None:
        return _builtin_constant_time_compare(val1, val2)

    len_eq = len(val1) == len(val2)
    if len_eq:
        result = 0
        left = val1
    else:
        result = 1
        left = val2
    for x, y in izip(bytearray(left), bytearray(val2)):
        result |= x ^ y
    return result == 0


def random_string(num_bytes, output_len=None):
    b = os.urandom(num_bytes)
    h = hashlib.sha256(b).digest()[:16]
    s = base64.b32encode(h).lower().replace('=', '')
    if not output_len:
        return s
    return s[:output_len]


def human_readable_filesize(b):
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


def is_root():
    return os.geteuid() == 0


def dir_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


class ZipWriter(object):
    def __init__(self, zip_filename=None):
        if zip_filename:
            self.zip_filename = zip_filename
        else:
            self.zip_filename = '{0:s}/onionshare_{1:s}.zip'.format(tempfile.mkdtemp(), random_string(4, 6))

        self.z = zipfile.ZipFile(self.zip_filename, 'w', allowZip64=True)

    def add_file(self, filename):
        self.z.write(filename, os.path.basename(filename), zipfile.ZIP_DEFLATED)

    def add_dir(self, filename):
        dir_to_strip = os.path.dirname(filename.rstrip('/'))+'/'
        for dirpath, dirnames, filenames in os.walk(filename):
            for f in filenames:
                full_filename = os.path.join(dirpath, f)
                if not os.path.islink(full_filename):
                    arc_filename = full_filename[len(dir_to_strip):]
                    self.z.write(full_filename, arc_filename, zipfile.ZIP_DEFLATED)

    def close(self):
        self.z.close()
