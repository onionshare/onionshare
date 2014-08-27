import os, inspect, hashlib, base64, hmac, platform
from itertools import izip

def get_platform():
    p = platform.system()
    if p == 'Linux' and platform.uname()[0:2] == ('Linux', 'amnesia'):
        p = 'Tails'
    return p

def get_onionshare_dir():
    if get_platform() == 'Darwin':
        onionshare_dir = os.path.dirname(__file__)
    else:
        onionshare_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    return onionshare_dir

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

def random_string(num_bytes):
    b = os.urandom(num_bytes)
    h = hashlib.sha256(b).digest()[:16]
    return base64.b32encode(h).lower().replace('=','')

def human_readable_filesize(b):
    thresh = 1024.0
    if b < thresh:
        return '{0} B'.format(b)
    units = ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB']
    u = 0
    b /= thresh
    while b >= thresh:
        b /= thresh
        u += 1
    return '{0} {1}'.format(round(b, 1), units[u])

def is_root():
    return os.geteuid() == 0

def file_crunching(filename):
    # calculate filehash, file size
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as f:
        buf = f.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(BLOCKSIZE)
    filehash = hasher.hexdigest()
    filesize = os.path.getsize(filename)
    return filehash, filesize


