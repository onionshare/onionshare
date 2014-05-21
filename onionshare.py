#!/usr/bin/env python

import os, sys, subprocess, time, hashlib, inspect
from random import randint
from functools import wraps

lib_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/lib'
sys.path.append(lib_path)

from stem.control import Controller
from stem import SocketError

from flask import Flask, Markup, Response, request, make_response, send_from_directory
app = Flask(__name__)

auth_username = auth_password = filename = filehash = filesize = ''

def check_auth(username, password):
    global auth_username, auth_password
    return username == auth_username and password == auth_password

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/")
@requires_auth
def index():
    global filename, filesize, filehash
    return "<html><head><title>OnionShare</title><style>body {{ background-color: #222222; color: #ffffff; text-align: center; font-family: arial; padding: 5em; }} a {{ color: #ffee00; text-decoration: none; }} a:hover{{ text-decoration: underline; }}</style></head><body><h1><a href='/download'>{0}</a></h1><p>SHA1 checksum: <strong>{1}</strong><br/>File size: <strong>{2} bytes</strong></p></body></html>".format(os.path.basename(filename), filehash, filesize)

@app.route("/download")
@requires_auth
def download():
    global filename
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return send_from_directory(dirname, basename, as_attachment=True)

def modify_firewall(port, open_port=True):
    if open_port:
        action = 'ACCEPT'
    else:
        action = 'REJECT'
    subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', action])

if __name__ == '__main__':
    # check for root
    if not os.geteuid()==0:
        sys.exit('You need to run this as root')

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

    # choose a port, username, and password
    port = randint(1025, 65535)
    auth_username = os.urandom(8).encode('hex')
    auth_password = os.urandom(8).encode('hex')

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
        ('HiddenServiceDir', '/tmp/onionshare_hidden_service_{0}/'.format(port)),
        ('HiddenServicePort', '80 127.0.0.1:{0}'.format(port))
    ])
    onion_host = open('/tmp/onionshare_hidden_service_{0}/hostname'.format(port), 'r').read().strip()

    # punch a hole in the firewall
    print 'Punching a hole in the firewall'
    modify_firewall(port)

    # instructions
    print '\nGive this information to the person you\'re sending the file to:'
    print 'URL: http://{0}/'.format(onion_host)
    print 'Username: {0}'.format(auth_username)
    print 'Password: {0}'.format(auth_password)
    print ''
    print 'Press Ctrl-C to stop server\n'

    # start the web server
    app.run(port=port)
    print '\n'

    # shutdown
    print 'Closing hole in firewall'
    modify_firewall(port, False)
