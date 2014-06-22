import os, sys, subprocess, time, hashlib, platform, json, locale, socket, argparse, Queue, inspect
from random import randint
from functools import wraps

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory, render_template_string

class NoTor(Exception):
    pass

app = Flask(__name__)

strings = {}
onionshare_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
slug = os.urandom(16).encode('hex')

# information about the file
filename = filesize = filehash = None
def set_file_info(new_filename, new_filehash, new_filesize):
    global filename, filehash, filesize
    filename = new_filename
    filehash = new_filehash
    filesize = new_filesize

REQUEST_LOAD = 0
REQUEST_DOWNLOAD = 1
REQUEST_PROGRESS = 2
REQUEST_OTHER = 3
q = Queue.Queue()

download_count = 0

def add_request(type, path, data=None):
    global q
    q.put({
      'type': type,
      'path': path,
      'data': data
    })

@app.route("/{0}".format(slug))
def index():
    global filename, filesize, filehash, slug, strings, REQUEST_LOAD
    add_request(REQUEST_LOAD, request.path)
    return render_template_string(open('{0}/index.html'.format(onionshare_dir)).read(),
        slug=slug, filename=os.path.basename(filename), filehash=filehash, filesize=filesize, strings=strings)

@app.route("/{0}/download".format(slug))
def download():
    global filename, filesize, q, download_count
    global REQUEST_DOWNLOAD, REQUEST_PROGRESS

    # each download has a unique id
    download_id = download_count
    download_count += 1

    # tell GUI the download started
    path = request.path
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
                add_request(REQUEST_PROGRESS, path, { 'id':download_id, 'bytes':fp.tell() })
        fp.close()

    r = Response(generate())
    r.headers.add('Content-Length', filesize)
    r.headers.add('Content-Disposition', 'attachment', filename=basename)
    return r

@app.errorhandler(404)
def page_not_found(e):
    global REQUEST_OTHER
    add_request(REQUEST_OTHER, request.path)
    return render_template_string(open('{0}/404.html'.format(onionshare_dir)).read())

def get_platform():
    p = platform.system()
    if p == 'Linux' and platform.uname()[0:2] == ('Linux', 'amnesia'):
        p = 'Tails'
    return p

def is_root():
    return os.geteuid() == 0

def tails_open_port(port):
    if get_platform() == 'Tails':
        print strings["punching_a_hole"]
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

def tails_close_port(port):
    if get_platform() == 'Tails':
        print strings["closing_hole"]
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'REJECT'])

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
    hidserv_dir_rand = os.urandom(8).encode('hex')
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
        raise NoTor(strings["cant_connect_ctrlport"].format(controlports))
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
        sys.exit(strings["tails_requires_root"])

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help='Do not attempt to use tor: for development only')
    parser.add_argument('filename', nargs=1)
    args = parser.parse_args()

    filename = os.path.abspath(args.filename[0])
    local_only = args.local_only

    if not (filename and os.path.isfile(filename)):
        sys.exit(strings["not_a_file"].format(filename))
    filename = os.path.abspath(filename)

    port = choose_port()
    local_host = "127.0.0.1:{0}".format(port)

    if not local_only:
        # try starting hidden service
        print strings["connecting_ctrlport"].format(port)
        try:
            onion_host = start_hidden_service(port)
        except NoTor as e:
            sys.exit(e.args[0])

    # startup
    print strings["calculating_sha1"]
    filehash, filesize = file_crunching(filename)
    set_file_info(filename, filehash, filesize)
    tails_open_port(port)
    print '\n' + strings["give_this_url"]
    if local_only:
        print 'http://{0}/{1}'.format(local_host, slug)
    else:
        print 'http://{0}/{1}'.format(onion_host, slug)
    print ''
    print strings["ctrlc_to_stop"]

    # start the web server
    app.run(port=port)
    print '\n'

    # shutdown
    tails_close_port(port)

if __name__ == '__main__':
    main()
