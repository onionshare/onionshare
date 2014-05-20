#!/usr/bin/env python

import os, sys, subprocess, time, hashlib
from random import randint

from functools import wraps
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

def reload_tor():
    subprocess.call(['/usr/sbin/service', 'tor', 'reload'])

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

    # load torrc
    torrc_path = '/etc/tor/torrc'
    if os.path.isfile(torrc_path):
        torrc = open(torrc_path).read()
    else:
        sys.exit('Error opening {0} for reading'.format(torrc_path));
    
    # choose a port to listen on
    port = randint(1025, 65535)

    # choose a random username and password
    auth_username = os.urandom(8).encode('hex')
    auth_password = os.urandom(8).encode('hex')

    # set up hidden service
    print 'Modifying torrc to configure hidden service on port {0}'.format(port)
    hidserv_dir = 'HiddenServiceDir /var/lib/tor/hidden_service_{0}/'.format(port)
    hidserv_port = 'HiddenServicePort 80 127.0.0.1:{0}'.format(port)
    open(torrc_path, 'a+').write("\n{0}\n{1}\n".format(hidserv_dir, hidserv_port))
    reload_tor()

    # punch a hole in the firewall
    print 'Punching a hole in the firewall'
    modify_firewall(port)

    # get hidden service hostname
    print 'Waiting 5 seconds for hidden service to get configured...'
    time.sleep(5)
    onion_host = open('/var/lib/tor/hidden_service_{0}/hostname'.format(port), 'r').read().strip()

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
    print 'Restoring original torrc'
    open(torrc_path, 'w').write(torrc)
    reload_tor()
    print 'Closing hole in firewall'
    modify_firewall(port, False)
