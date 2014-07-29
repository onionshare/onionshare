# -*- coding: utf-8 -*-
import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect, base64
from random import randint
from functools import wraps

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory, render_template_string, abort

from werkzeug.utils import secure_filename
# Flask depends on itsdangerous, which needs constant time string comparison
# for the HMAC values in secure cookies. Since we know itsdangerous is
# available, we just use its function.
from itsdangerous import constant_time_compare

class NoTor(Exception):
    pass

def random_string(num_bytes):
    b = os.urandom(num_bytes)
    h = hashlib.sha256(b).digest()[:16]
    return base64.b32encode(h).lower().replace('=','')

def get_platform():
    p = platform.system()
    if p == 'Linux' and platform.uname()[0:2] == ('Linux', 'amnesia'):
        p = 'Tails'
    return p

# information about the file
filename = filesize = filehash = None
def set_file_info(new_filename, new_filehash, new_filesize):
    global filename, filehash, filesize
    filename = new_filename
    filehash = new_filehash
    filesize = new_filesize

# automatically close
stay_open = False
def set_stay_open(new_stay_open):
    global stay_open
    stay_open = new_stay_open

app = Flask(__name__)

def debug_mode():
    import logging
    global app

    if platform.system() == 'Windows':
        temp_dir = os.environ['Temp'].replace('\\', '/')
    else:
        temp_dir = '/tmp/'

    log_handler = logging.FileHandler('{0}/onionshare_server.log'.format(temp_dir))
    log_handler.setLevel(logging.WARNING)
    app.logger.addHandler(log_handler)

# get path of onioshare directory
if get_platform() == 'Darwin':
    onionshare_dir = os.path.dirname(__file__)
else:
    onionshare_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

strings = {}
slug = random_string(16)
download_count = 0

REQUEST_LOAD = 0
REQUEST_DOWNLOAD = 1
REQUEST_PROGRESS = 2
REQUEST_OTHER = 3
q = Queue.Queue()

def add_request(type, path, data=None):
    global q
    q.put({
      'type': type,
      'path': path,
      'data': data
    })

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

@app.route("/<slug_candidate>")
def index(slug_candidate):
    global filename, filesize, filehash, slug, strings, REQUEST_LOAD, onionshare_dir

    if not constant_time_compare(slug.encode('ascii'), slug_candidate.encode('ascii')):
        abort(404)

    add_request(REQUEST_LOAD, request.path)
    return render_template_string(
        open('{0}/index.html'.format(onionshare_dir)).read(),
        slug=slug,
        filename=os.path.basename(filename),
        filehash=filehash,
        filesize=filesize,
        filesize_human=human_readable_filesize(filesize),
        strings=strings
    )

@app.route("/<slug_candidate>/download")
def download(slug_candidate):
    global filename, filesize, q, download_count
    global REQUEST_DOWNLOAD, REQUEST_PROGRESS

    if not constant_time_compare(slug.encode('ascii'), slug_candidate.encode('ascii')):
        abort(404)

    # each download has a unique id
    download_id = download_count
    download_count += 1

    # prepare some variables to use inside generate() function below
    # which is outsie of the request context
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    path = request.path

    # tell GUI the download started
    add_request(REQUEST_DOWNLOAD, path, { 'id':download_id })

    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)

    def generate():
        chunk_size = 102400 # 100kb

        fp = open(filename, 'rb')
        done = False
        while not done:
            chunk = fp.read(102400)
            if chunk == '':
                done = True
            else:
                yield chunk

                # tell GUI the progress
                downloaded_bytes = fp.tell()
                percent = round((1.0 * downloaded_bytes / filesize) * 100, 2);
                sys.stdout.write("\r{0}, {1}%          ".format(human_readable_filesize(downloaded_bytes), percent))
                sys.stdout.flush()
                add_request(REQUEST_PROGRESS, path, { 'id':download_id, 'bytes':downloaded_bytes })

        fp.close()
        sys.stdout.write("\n")

        # download is finished, close the server
        global stay_open
        if not stay_open:
            print "Closing automatically because download finished"
            if shutdown_func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            shutdown_func()

    r = Response(generate())
    r.headers.add('Content-Length', filesize)
    r.headers.add('Content-Disposition', 'attachment', filename=basename)
    return r

receive_allowed = False
@app.route("/send/function", methods=['GET', 'POST'])
def receive_file(allowed):
    if request.method == 'POST' and allowed:
        file = request.files['file']
        filename = secure_filename(file)
        # TODO: make destination customizable
        file.save(os.path.join("C:/users/"+os.environ.get("USERNAME")+"/Desktop/", filename))

@app.route("/send")
def serve_send_index():
    global onionshare_dir
    return render_template_string(open('{0}/receive_mode.html'.format(onionshare_dir)).read())

@app.errorhandler(404)
def page_not_found(e):
    global REQUEST_OTHER, onionshare_dir
    add_request(REQUEST_OTHER, request.path)
    return render_template_string(open('{0}/404.html'.format(onionshare_dir)).read())

def is_root():
    return os.geteuid() == 0

def tails_open_port(port):
    if get_platform() == 'Tails':
        print translated("punching_a_hole")
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

def tails_close_port(port):
    if get_platform() == 'Tails':
        print translated("closing_hole")
        subprocess.call(['/sbin/iptables', '-D', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

def load_strings(default="en"):
    global strings
    try:
        translated = json.loads(open('{0}/strings.json'.format(os.getcwd())).read())
    except IOError:
        translated = json.loads(open('{0}/strings.json'.format(onionshare_dir)).read())
    strings = translated[default]
    lc, enc = locale.getdefaultlocale()
    if lc:
        lang = lc[:2]
        if lang in translated:
            # if a string doesn't exist, fallback to English
            for key in translated[default]:
                if key in translated[lang]:
                    strings[key] = translated[lang][key]
    return strings

def translated(k):
    return strings[k].encode("utf-8")

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

def choose_port():
    # let the OS choose a port
    tmpsock = socket.socket()
    tmpsock.bind(("127.0.0.1", 0))
    port = tmpsock.getsockname()[1]
    tmpsock.close()
    return port

def start_hidden_service(port):
    # come up with a hidden service directory name
    hidserv_dir_rand = random_string(8)
    if get_platform() == "Windows":
        if 'Temp' in os.environ:
            temp = os.environ['Temp'].replace('\\', '/')
        else:
            temp = 'C:/tmp'
        hidserv_dir = "{0}/onionshare_{1}".format(temp, hidserv_dir_rand)
    else:
        hidserv_dir = "/tmp/onionshare_{0}".format(hidserv_dir_rand)

    # connect to the tor controlport
    controlports = [9051, 9151]
    controller = False
    for controlport in controlports:
        try:
            controller = Controller.from_port(port=controlport)
        except SocketError:
            pass
    if not controller:
        raise NoTor(translated("cant_connect_ctrlport").format(controlports, "is Tor running?"))

    controller.authenticate()

    # set up hidden service
    controller.set_options([
        ('HiddenServiceDir', hidserv_dir),
        ('HiddenServicePort', '80 127.0.0.1:{0}'.format(port))
    ])

    # figure out the .onion hostname
    hostname_file = '{0}/hostname'.format(hidserv_dir)
    onion_host = open(hostname_file, 'r').read().strip()

    return onion_host

def main():
    load_strings()

    # check for root in Tails
    if get_platform() == 'Tails' and not is_root():
        sys.exit(translated("tails_requires_root"))

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help='Do not attempt to use tor: for development only')
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help='Keep hidden service running after download has finished')
    parser.add_argument('--debug', action='store_true', dest='debug', help='Log errors to disk')
    required = parser.add_mutually_exclusive_group(required=True)
    required.add_argument('--receive', action='store_true', help='Allows the user of Onionshare to receive files from non-users')
    required.add_argument('--filename', nargs=1, help='File to share')
    args = parser.parse_args()

    filename = ''
    local_only = bool(args.local_only)
    debug = bool(args.debug)
    receiver_mode = bool(args.receive)

    if receiver_mode:
        global receive_allowed
        receive_allowed = True
    else:
        filename = os.path.abspath(args.filename[0])

    if debug:
        debug_mode()

    global stay_open
    stay_open = bool(args.stay_open)

    if not (filename and os.path.isfile(filename)) and not receiver_mode:
        sys.exit(translated("not_a_file").format(filename))
    if not receiver_mode:
        filename = os.path.abspath(filename)

    port = choose_port()
    local_host = "127.0.0.1:{0}".format(port)

    if not local_only:
        # try starting hidden service
        print translated("connecting_ctrlport").format(port)
        try:
            onion_host = start_hidden_service(port)
        except NoTor as e:
            sys.exit(e.args[0])

    # startup
    if not receiver_mode:
        print translated("calculating_sha1")
        filehash, filesize = file_crunching(filename)
        set_file_info(filename, filehash, filesize)
    tails_open_port(port)
    print '\n' + translated("give_this_url")
    if local_only:
        print 'http://{0}/{1}'.format(local_host, slug)
    elif not receiver_mode:
        print 'http://{0}/{1}'.format(onion_host, slug)
    else:
        print 'http://{0}/'.format(onion_host)
    print ''
    print translated("ctrlc_to_stop")

    # start the web server
    app.run(port=port)
    print '\n'

    # shutdown
    tails_close_port(port)

if __name__ == '__main__':
    main()
