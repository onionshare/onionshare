#!/usr/bin/env python

import os, sys, subprocess, time, hashlib, platform, json, locale
from random import randint
from functools import wraps

sys.path.append(os.path.dirname(__file__)+'/lib')

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory, render_template_string
app = Flask(__name__)

strings = {}

# generate an unguessable string
slug = os.urandom(16).encode('hex')

# file information
filename = filehash = filesize = ''

@app.route("/{0}".format(slug))
def index():
    global filename, filesize, filehash, slug
    return render_template_string(open('{0}/index.html'.format(os.path.dirname(__file__))).read(),
        slug=slug, filename=os.path.basename(filename), filehash=filehash, filesize=filesize, strings=strings)

@app.route("/{0}/download".format(slug))
def download():
    global filename
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return send_from_directory(dirname, basename, as_attachment=True)

@app.errorhandler(404)
def page_not_found(e):
    return render_template_string(open('{0}/404.html'.format(os.path.dirname(__file__))).read())

def get_platform():
    if 'ONIONSHARE_PLATFORM' in os.environ:
        return os.environ['ONIONSHARE_PLATFORM']
    else:
        return platform.system()

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

if __name__ == '__main__':
    load_strings()
    # validate filename
    if len(sys.argv) != 2:
        sys.exit('Usage: {0} [filename]'.format(sys.argv[0]));
    filename = sys.argv[1]
    if not os.path.isfile(filename):
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

    # choose a port
    port = randint(1025, 65535)

    # connect to the tor controlport
    print strings["connecting_ctrlport"].format(port)
    controlports = [9051, 9151]
    controller = False
    for controlport in controlports:
        try:
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
    print 'http://{0}/{1}'.format(onion_host, slug)
    print ''
    print strings["ctrlc_to_stop"]

    # start the web server
    app.run(port=port)
    print '\n'

    # shutdown
    tails_close_port(port)
