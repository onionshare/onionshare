import os, sys, subprocess, time, hashlib, platform, json, locale, socket, re, argparse
from random import randint
from functools import wraps

def get_platform():
    if 'ONIONSHARE_PLATFORM' in os.environ:
        return os.environ['ONIONSHARE_PLATFORM']
    else:
        return platform.system()

if get_platform() == 'Tails':
    sys.path.append(os.path.dirname(__file__)+'/../tails/lib')

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory, render_template_string

app = Flask(__name__)

strings = {}

# generate an unguessable string
slug = os.urandom(16).encode('hex')

# file information
filename = filehash = filesize = ''

@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response

def send_file_partial(range_header):
    global filename

    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)

    size = os.path.getsize(filename)
    byte1, byte2 = 0, None
    
    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()
    
    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = (byte2 - byte1) + 1
    
    data = None
    with open(filename, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data,
        206,
        # mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True)
    rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))

    return rv


@app.route("/{0}".format(slug))
def index():
    global filename, filesize, filehash, slug, strings
    return render_template_string(open('{0}/index.html'.format(os.path.dirname(__file__))).read(),
        slug=slug, filename=os.path.basename(filename), filehash=filehash, filesize=filesize, strings=strings)

@app.route("/{0}/download".format(slug))
def download():
    global filename

    range_header = request.headers.get('Range', None)
    if range_header:
        return send_file_partial(range_header)
    
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return send_from_directory(dirname, basename, as_attachment=True)

@app.errorhandler(404)
def page_not_found(e):
    return render_template_string(open('{0}/404.html'.format(os.path.dirname(__file__))).read())

def get_hidden_service_dir(port):
    if get_platform() == "Windows":
        if 'Temp' in os.environ:
            temp = os.environ['Temp'].replace('\\', '/')
        else:
            temp = 'C:/tmp'
        return "{0}/onionshare_hidden_service_{1}".format(temp, port)

    return "/tmp/onionshare_hidden_service_{0}".format(port)

def get_hidden_service_hostname(port):
    hostname_file = '{0}/hostname'.format(get_hidden_service_dir(port))
    return open(hostname_file, 'r').read().strip()

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
    translated = json.loads(open('{0}/strings.json'.format(
        os.path.dirname(__file__))).read())
    strings = translated[default]
    lc, enc = locale.getdefaultlocale()
    if lc:
        lang = lc[:2]
        if lang in translated:
            strings = translated[lang]

def main():
    global filename, filehash, filesize
    load_strings()

    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help='Do not attempt to use tor: for development only')
    parser.add_argument('filename', nargs=1)
    args = parser.parse_args()
    
    filename = os.path.abspath(args.filename[0])
    local_only = args.local_only
    
    if not (filename and os.path.isfile(filename)):
        sys.exit(strings["not_a_file"].format(filename))

    # calculate filehash, file size
    print strings["calculating_sha1"]
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as f:
        buf = f.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(BLOCKSIZE)
    filehash = hasher.hexdigest()
    filesize = os.path.getsize(filename)

    # let the OS choose a port
    tmpsock = socket.socket()
    tmpsock.bind(("127.0.0.1", 0))
    port = tmpsock.getsockname()[1]
    tmpsock.close()

    local_host = "127.0.0.1:{0}".format(port)

    if not local_only:
        # connect to the tor controlport
        print strings["connecting_ctrlport"].format(port)
        controlports = [9051, 9151]
        controller = False

        for controlport in controlports:
            try:
                if not controller:
                    controller = Controller.from_port(port=controlport)
            except SocketError:
                pass

        if not controller:
            sys.exit(strings["cant_connect_ctrlport"].format(controlports))

        controller.authenticate()
            
        # set up hidden service
        controller.set_options([
            ('HiddenServiceDir', get_hidden_service_dir(port)),
            ('HiddenServicePort', '80 127.0.0.1:{0}'.format(port))
        ])
        onion_host = get_hidden_service_hostname(port)
        
        # punch a hole in the firewall
        tails_open_port(port)
                    
    # instructions
    print '\n' + strings["give_this_url"]
    if local_only:
        print 'http://{0}/{1}'.format(local_host, slug)
    else:
        print 'http://{0}/{1}'.format(onion_host, slug)
    print ''
    print strings["ctrlc_to_stop"]
                    
    # start the web server
    app.run(port=port, debug=True)
    print '\n'
    
    # shutdown
    tails_close_port(port)
    
    if __name__ == '__main__':
        main()
