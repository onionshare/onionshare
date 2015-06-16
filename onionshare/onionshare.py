# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
import os, sys, subprocess, time, argparse, inspect, shutil, socket, threading, urllib2, httplib, tempfile
import socks

from stem.control import Controller

import strings, helpers, web


class NoTor(Exception):
    pass


class TailsError(Exception):
    pass


class HSDirError(Exception):
    pass


def hsdic2list(dic):
    """Convert what we get from get_conf_map to what we need for set_options"""
    return [
        pair for pairs in [
            [('HiddenServiceDir', vals[0]), ('HiddenServicePort', vals[1])]
            for vals in zip(dic.get('HiddenServiceDir', []), dic.get('HiddenServicePort', []))
        ] for pair in pairs
    ]


class OnionShare(object):
    def __init__(self, debug=False, local_only=False, stay_open=False):
        self.port = None
        self.controller = None
        self.hidserv_dir = None

        # debug mode
        if debug:
            web.debug_mode()

        # do not use tor -- for development
        self.local_only = local_only

        # automatically close when download is finished
        self.stay_open = stay_open

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []

    def cleanup(self):
        # cleanup hidden service
        try:
            if self.controller:
                # Get fresh hidden services (maybe changed since last time)
                # and remove ourselves
                hsdic = self.controller.get_conf_map('HiddenServiceOptions') or {
                    'HiddenServiceDir': [], 'HiddenServicePort': []
                }
                if self.hidserv_dir and self.hidserv_dir in hsdic.get('HiddenServiceDir', []):
                    dropme = hsdic['HiddenServiceDir'].index(self.hidserv_dir)
                    del hsdic['HiddenServiceDir'][dropme]
                    del hsdic['HiddenServicePort'][dropme]
                    self.controller.set_options(hsdic2list(hsdic))
                # Politely close the controller
                self.controller.close()
        except:
            pass

        # cleanup files
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

    def start_hidden_service(self, gui=False, tails_root=False):
        if not self.port:
            self.choose_port()

        if helpers.get_platform() == 'Tails' and not tails_root:
            # in Tails, start the hidden service in a root process
            if gui:
                args = ['/usr/bin/gksudo', '-D', 'OnionShare', '--', '/usr/bin/onionshare']
            else:
                args = ['/usr/bin/sudo', '--', '/usr/bin/onionshare']
            print "Executing: {0:s}".format(args+[str(self.port)])
            p = subprocess.Popen(args+[str(self.port)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout = p.stdout.read(22) # .onion URLs are 22 chars long

            if stdout:
                self.onion_host = stdout
                print 'Got onion_host: {0:s}'.format(self.onion_host)
            else:
                if p.poll() == -1:
                    raise TailsError(o.stderr.read())
                else:
                    raise TailsError(strings._("error_tails_unknown_root"))

        else:
            if self.local_only:
                self.onion_host = '127.0.0.1:{0:d}'.format(self.port)

            else:
                # come up with a hidden service directory name
                if helpers.get_platform() == 'Tails':
                    # need to create HS directory in /var/lib/tor because of AppArmor rules included in Tails
                    self.hidserv_dir = tempfile.mkdtemp(dir='/var/lib/tor')

                    # change owner to debian-tor
                    import pwd
                    import grp
                    uid = pwd.getpwnam("debian-tor").pw_uid
                    gid = grp.getgrnam("debian-tor").gr_gid
                    os.chown(self.hidserv_dir, uid, gid)
                else:
                    # in non-Tails linux, onionshare will create HS dir in /tmp/onionshare/*
                    path = '/tmp/onionshare'
                    try:
                        if not os.path.exists(path):
                            os.makedirs(path, 0700)
                    except:
                        raise HSDirError(strings._("error_hs_dir_cannot_create").format(path))
                    if not os.access(path, os.W_OK):
                        raise HSDirError(strings._("error_hs_dir_not_writable").format(path))

                    self.hidserv_dir = tempfile.mkdtemp(dir=path)
                self.cleanup_filenames.append(self.hidserv_dir)

                # connect to the tor controlport
                self.controller = None
                tor_control_ports = [9051, 9151]
                for tor_control_port in tor_control_ports:
                    try:
                        self.controller = Controller.from_port(port=tor_control_port)
                        self.controller.authenticate()
                        break
                    except:
                        pass
                if not self.controller:
                    raise NoTor(strings._("cant_connect_ctrlport").format(tor_control_ports))

                # set up hidden service
                if helpers.get_platform() == 'Windows':
                    self.hidserv_dir = self.hidserv_dir.replace('\\', '/')
                hsdic = self.controller.get_conf_map('HiddenServiceOptions') or {
                    'HiddenServiceDir': [], 'HiddenServicePort': []
                }
                if self.hidserv_dir in hsdic.get('HiddenServiceDir', []):
                    # Maybe a stale service with the wrong local port
                    dropme = hsdic['HiddenServiceDir'].index(self.hidserv_dir)
                    del hsdic['HiddenServiceDir'][dropme]
                    del hsdic['HiddenServicePort'][dropme]
                hsdic['HiddenServiceDir'] = hsdic.get('HiddenServiceDir', [])+[self.hidserv_dir]
                hsdic['HiddenServicePort'] = hsdic.get('HiddenServicePort', [])+[
                    '80 127.0.0.1:{0:d}'.format(self.port)]

                self.controller.set_options(hsdic2list(hsdic))

                # figure out the .onion hostname
                hostname_file = '{0:s}/hostname'.format(self.hidserv_dir)
                self.onion_host = open(hostname_file, 'r').read().strip()

    def wait_for_hs(self):
        if self.local_only:
            return True

        print strings._('wait_for_hs')

        ready = False
        while not ready:
            try:
                sys.stdout.write('{0:s} '.format(strings._('wait_for_hs_trying')))
                sys.stdout.flush()

                if helpers.get_platform() == 'Tails':
                    # in Tails everything is proxies over Tor already
                    # so no need to set the socks5 proxy
                    urllib2.urlopen('http://{0:s}'.format(self.onion_host))
                else:
                    tor_exists = False
                    tor_socks_ports = [9050, 9150]
                    for tor_socks_port in tor_socks_ports:
                        try:
                            s = socks.socksocket()
                            s.setproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', tor_socks_port)
                            s.connect((self.onion_host, 80))
                            s.close()
                            tor_exists = True
                            break
                        except socks.ProxyConnectionError:
                            pass
                    if not tor_exists:
                        raise NoTor(strings._("cant_connect_socksport").format(tor_socks_ports))
                ready = True

                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_yup')))
            except socks.SOCKS5Error:  # non-Tails error
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except urllib2.HTTPError:  # Tails error
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except httplib.BadStatusLine: # Tails (with bridge) error
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except KeyboardInterrupt:
                return False
        return True


def tails_root():
    # if running in Tails and as root, do only the things that require root
    if helpers.get_platform() == 'Tails' and helpers.is_root():
        parser = argparse.ArgumentParser()
        parser.add_argument('port', nargs=1, help=strings._("help_tails_port"))
        args = parser.parse_args()

        try:
            port = int(args.port[0])
        except ValueError:
            sys.stderr.write('{0:s}\n'.format(strings._("error_tails_invalid_port")))
            sys.exit(-1)

        # open hole in firewall
        subprocess.call(['/sbin/iptables', '-I', 'OUTPUT', '-o', 'lo',
                         '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])

        # start hidden service
        app = OnionShare()
        app.choose_port()
        app.port = port
        app.start_hidden_service(False, True)
        sys.stdout.write(app.onion_host)
        sys.stdout.flush()

        # close hole in firewall on shutdown
        import signal

        def handler(signum=None, frame=None):
            subprocess.call(['/sbin/iptables', '-D', 'OUTPUT', '-o', 'lo',
                             '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'])
            sys.exit()
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, handler)

        # stay open until killed
        while True:
            time.sleep(1)


def main(cwd=None):
    strings.load_strings()

    # onionshare CLI in OSX needs to change current working directory (#132)
    if helpers.get_platform() == 'Darwin':
        if cwd:
            os.chdir(cwd)

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
        app.choose_port()
        print strings._("connecting_ctrlport").format(int(app.port))
        app.start_hidden_service()
    except NoTor as e:
        sys.exit(e.args[0])
    except TailsError as e:
        sys.exit(e.args[0])
    except HSDirError as e:
        sys.exit(e.args[0])

    # prepare files to share
    print strings._("preparing_files")
    web.set_file_info(filenames)
    app.cleanup_filenames.append(web.zip_filename)

    # warn about sending large files over Tor
    if web.zip_filesize >= 157286400:  # 150mb
        print ''
        print strings._("large_filesize")
        print ''

    # start onionshare service in new thread
    t = threading.Thread(target=web.start, args=(app.port, app.stay_open))
    t.daemon = True
    t.start()

    try:  # Trap Ctrl-C
        # wait for hs
        ready = app.wait_for_hs()
        if not ready:
            sys.exit()

        print strings._("give_this_url")
        print 'http://{0:s}/{1:s}'.format(app.onion_host, web.slug)
        print ''
        print strings._("ctrlc_to_stop")

        # wait for app to close
        while t.is_alive():
            # t.join() can't catch KeyboardInterrupt in such as Ubuntu
            t.join(0.5)
    except KeyboardInterrupt:
        web.stop(app.port)
    finally:
        # shutdown
        app.cleanup()

if __name__ == '__main__':
    main()
