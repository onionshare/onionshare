#!/usr/bin/env python

import os, sys, subprocess, time, hashlib, inspect, platform
from random import randint
from functools import wraps

lib_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/lib'
sys.path.append(lib_path)

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory
app = Flask(__name__)

# generate an unguessable string
slug = os.urandom(16).encode('hex')

# file information
filename = filehash = filesize = ''

@app.route("/{0}".format(slug))
def index():
    global filename, filesize, filehash, slug
    return "<html><head><title>OnionShare</title><style>body {{ background-color: #222222; color: #ffffff; text-align: center; font-family: arial; padding: 5em; }} a {{ color: #ffee00; text-decoration: none; }} a:hover{{ text-decoration: underline; }}</style></head><body><h1><a href='/{0}/download'>{1}</a></h1><p>SHA1 checksum: <strong>{2}</strong><br/>File size: <strong>{3} bytes</strong></p></body></html>".format(slug, os.path.basename(filename), filehash, filesize)

@app.route("/{0}/download".format(slug))
def download():
    global filename
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return send_from_directory(dirname, basename, as_attachment=True)

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
        print 'Punching a hole in the firewall'
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

def tails_close_port(port):
    if get_platform() == 'Tails':
        print 'Closing hole in firewall'
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'REJECT'])

if __name__ == '__main__':
    # validate filename
    if len(sys.argv) != 2:
        sys.exit('Usage: {0} [filename]'.format(sys.argv[0]));
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        sys.exit('{0} is not a file'.format(filename))

    # calculate filehash, file size
    sha1 = hashlib.sha1()
    f = open(filename, 'rb')
    try:
        sha1.update(f.read())
    finally:
        f.close()
    filehash = sha1.hexdigest()
    filesize = os.path.getsize(filename)

    # choose a port
    port = randint(1025, 65535)

    # connect to the tor controlport
    print 'Connecting to Tor ControlPort to set up hidden service on port {0}'.format(port)
    controlports = [9051, 9151]
    controller = False
    for controlport in controlports:
        try:
            controller = Controller.from_port(port=controlport)
        except SocketError:
            pass
    if not controller:
        sys.exit('Cannot connect to Tor ControlPorts on ports {0}. Is Tor running?'.format(controlports))
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
    print '\nGive this URL to the person you\'re sending the file to:'
    print 'http://{0}/{1}'.format(onion_host, slug)
    print ''
    print 'Press Ctrl-C to stop server\n'

    # start the web server
    app.run(port=port)
    print '\n'

    # shutdown
    tails_close_port(port)
