# -*- coding: utf-8 -*-
import os, sys, subprocess, time, argparse, inspect, shutil, socket

from stem.control import Controller
from stem import SocketError

import strings, helpers, web

class NoTor(Exception): pass
class TailsError(Exception): pass

class OnionShare(object):
    def __init__(self, debug=False, local_only=False, stay_open=False):
        # debug mode
        if debug:
            web.debug_mode()

        # do not use tor -- for development
        self.local_only = local_only

        # automatically close when download is finished
        self.stay_open = stay_open

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []

        # choose a random port
        self.choose_port()
        self.local_host = "127.0.0.1:{0}".format(self.port)

    def cleanup(self):
        for filename in self.cleanup_filenames:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                shutil.rmtree(filename)
        self.cleanup_filenames = []

    def choose_port(self):
        # let the OS choose a port
        tmpsock = socket.socket()
        tmpsock.bind(("127.0.0.1", 0))
        self.port = tmpsock.getsockname()[1]
        tmpsock.close()

    def start_hidden_service(self, gui=False):
        if helpers.get_platform() == 'Tails':
            # in Tails, start the hidden service in a root process
            if gui:
                args = ['/usr/bin/gksudo', '-D', 'OnionShare', '--', '/usr/bin/onionshare']
            else:
                args = ['/usr/bin/sudo', '--', '/usr/bin/onionshare']
            p = subprocess.Popen(args+[str(app.port)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout = p.stdout.read(22) # .onion URLs are 22 chars long

            if stdout:
                self.onion_host = stdout
            else:
                if root_p.poll() == -1:
                    raise TailsError(o.stderr.read())
                else:
                    raise TailsError(strings._("error_tails_unknown_root"))

        else:
            if self.local_only:
                self.onion_host = '127.0.0.1:{0}'.format(self.port)

            else:
                print strings._("connecting_ctrlport").format(self.port)

                # come up with a hidden service directory name
                hidserv_dir = '{0}/onionshare_{1}'.format(helpers.get_tmp_dir(), helpers.random_string(8))
                self.cleanup_filenames.append(hidserv_dir)

                # connect to the tor controlport
                controlports = [9051, 9151]
                controller = False
                for controlport in controlports:
                    try:
                        controller = Controller.from_port(port=controlport)
                    except SocketError:
                        pass
                if not controller:
                    raise NoTor(strings._("cant_connect_ctrlport").format(controlports))
                controller.authenticate()

                # set up hidden service
                controller.set_options([
                    ('HiddenServiceDir', hidserv_dir),
                    ('HiddenServicePort', '80 127.0.0.1:{0}'.format(self.port))
                ])

                # figure out the .onion hostname
                hostname_file = '{0}/hostname'.format(hidserv_dir)
                self.onion_host = open(hostname_file, 'r').read().strip()

def tails_root():
    # if running in Tails and as root, do only the things that require root
    if helpers.get_platform() == 'Tails' and helpers.is_root():
        parser = argparse.ArgumentParser()
        parser.add_argument('port', nargs=1, help=strings._("help_tails_port"))
        args = parser.parse_args()

        try:
            port = int(args.port[0])
        except ValueError:
            sys.stderr.write('{0}\n'.format(strings._("error_tails_invalid_port")))
            sys.exit(-1)

        # open hole in firewall
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

        # start hidden service
        onion_host = start_hidden_service(port)
        sys.stdout.write(onion_host)
        sys.stdout.flush()

        # close hole in firewall on shutdown
        import signal
        def handler(signum = None, frame = None):
            subprocess.call(['/sbin/iptables', '-D', 'OUTPUT', '-o', 'lo', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])
            sys.exit()
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, handler)

        # stay open until killed
        while True:
            time.sleep(1)

def main():
    strings.load_strings()
    tails_root()

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-only', action='store_true', dest='local_only', help=strings._("help_local_only"))
    parser.add_argument('--stay-open', action='store_true', dest='stay_open', help=strings._("help_stay_open"))
    parser.add_argument('--debug', action='store_true', dest='debug', help=strings._("help_debug"))
    parser.add_argument('filename', metavar='filename', nargs='+', help=strings._('help_filename'))
    args = parser.parse_args()

    filenames = args.filename
    for i in range(len(filenames)):
        filenames[i] = os.path.abspath(filenames[i])

    local_only = bool(args.local_only)
    debug = bool(args.debug)
    stay_open = bool(args.stay_open)

    # validation
    valid = True
    for filename in filenames:
        if not os.path.exists(filename):
            print(strings._("not_a_file").format(filename))
            valid = False
    if not valid:
        sys.exit()

    # start the onionshare app
    try:
        app = OnionShare(debug, local_only, stay_open)
        app.start_hidden_service()
    except NoTor as e:
        sys.exit(e.args[0])
    except TailsError as e:
        sys.exit(e.args[0])

    # startup
    web.set_file_info(filenames)
    app.cleanup_filenames.append(web.zip_filename)
    print strings._("give_this_url")
    print 'http://{0}/{1}'.format(app.onion_host, web.slug)
    print ''
    print strings._("ctrlc_to_stop")

    # start the web server
    web.start(app.port, app.stay_open)
    print '\n'

    # shutdown
    app.cleanup()

if __name__ == '__main__':
    main()
