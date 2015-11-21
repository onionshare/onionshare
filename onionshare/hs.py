# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2015 Micah Lee <micah@micahflee.com>

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

from stem.control import Controller
import os, sys, tempfile, shutil, urllib2, httplib
import socks

import helpers, strings

class NoTor(Exception):
    """
    This exception is raised if onionshare can't find a Tor control port
    to connect to, or if it can't find a Tor socks5 proxy to proxy though.
    """
    pass

class HSDirError(Exception):
    """
    This exception is raised when onionshare tries create a non-ephemeral
    hidden service and does not have permission to create or write to
    the hidden service directory.
    """
    pass

class HS(object):
    """
    HS is an abstraction layer for connecting to the Tor control port and
    creating hidden services. Onionshare supports creating hidden services
    using two methods:

    - Modifying the Tor configuration through the control port is the old
      method, and will be deprecated in favor of ephemeral hidden services.
    - Using the control port to create ephemeral hidden servers is the
      preferred method.

    This class detects the versions of Tor and stem to determine if ephemeral
    hidden services are supported. If not, it falls back to modifying the
    Tor configuration.
    """
    def __init__(self, transparent_torification=False):
        self.transparent_torification = transparent_torification

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []
        self.service_id = None

        # connect to the tor controlport
        self.c = None
        ports = [9151, 9153, 9051]
        for port in ports:
            try:
                self.c = Controller.from_port(port=port)
                self.c.authenticate()
                break
            except:
                pass
        if not self.c:
            raise NoTor(strings._("cant_connect_ctrlport").format(ports))

        # do the versions of stem and tor that I'm using support ephemeral hidden services?
        tor_version = self.c.get_version().version_str
        list_ephemeral_hidden_services = getattr(self.c, "list_ephemeral_hidden_services", None)
        self.supports_ephemeral = callable(list_ephemeral_hidden_services) and tor_version >= '0.2.7.1'

    def start(self, port):
        """
        Start a hidden service on port 80, pointing to the given port, and
        return the onion hostname.
        """
        print strings._("connecting_ctrlport").format(int(port))
        if self.supports_ephemeral:
            print strings._('using_ephemeral')
            res = self.c.create_ephemeral_hidden_service({ 80: port }, await_publication = True)
            self.service_id = res.content()[0][2].split('=')[1]
            onion_host = res.content()[0][2].split('=')[1] + '.onion'
            return onion_host

        else:
            # come up with a hidden service directory name
            if helpers.get_platform() == 'Windows':
                path = '{0:s}/onionshare'.format(os.environ['Temp'].replace('\\', '/'))
            else:
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

            # set up hidden service
            hs_conf = self.c.get_hidden_service_conf()
            if self.hidserv_dir in hs_conf:
                del hs_conf[self.hidserv_dir]
            hs_conf[self.hidserv_dir] = {'HiddenServicePort': [(80, '127.0.0.1', port)]}
            self.c.set_hidden_service_conf(hs_conf)

            # figure out the .onion hostname
            hostname_file = '{0:s}/hostname'.format(self.hidserv_dir)
            onion_host = open(hostname_file, 'r').read().strip()
            return onion_host

    def wait_for_hs(self, onion_host):
        """
        This function is only required when using non-ephemeral hidden services. After
        creating a hidden service, continually attempt to connect to it until it
        successfully connects..
        """
        # legacy only, this function is no longer required with ephemeral hidden services
        print strings._('wait_for_hs')

        ready = False
        while not ready:
            try:
                sys.stdout.write('{0:s} '.format(strings._('wait_for_hs_trying')))
                sys.stdout.flush()

                if self.transparent_torification:
                    # no need to set the socks5 proxy
                    urllib2.urlopen('http://{0:s}'.format(onion_host))
                else:
                    tor_exists = False
                    ports = [9150, 9152, 9050]
                    for port in ports:
                        try:
                            s = socks.socksocket()
                            s.setproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', port)
                            s.connect((onion_host, 80))
                            s.close()
                            tor_exists = True
                            break
                        except socks.ProxyConnectionError:
                            pass
                    if not tor_exists:
                        raise NoTor(strings._("cant_connect_socksport").format(tor_socks_ports))
                ready = True

                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_yup')))
            except socks.SOCKS5Error:
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except urllib2.HTTPError:  # torification error
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except httplib.BadStatusLine: # torification (with bridge) error
                sys.stdout.write('{0:s}\n'.format(strings._('wait_for_hs_nope')))
                sys.stdout.flush()
            except KeyboardInterrupt:
                return False
        return True

    def cleanup(self):
        """
        Stop hidden services that were created earlier, and delete any temporary
        files that were created.
        """
        if self.supports_ephemeral:
            # cleanup the ephemeral hidden service
            if self.service_id:
                self.c.remove_ephemeral_hidden_service(self.service_id)
                self.service_id = None

        else:
            # cleanup hidden service
            try:
                if self.c:
                    # Get fresh hidden services (maybe changed since last time)
                    # and remove ourselves
                    hs_conf = self.c.get_hidden_service_conf()
                    if self.hidserv_dir in hs_conf:
                        del hs_conf[self.hidserv_dir]
                    self.c.set_hidden_service_conf(hs_conf)
                    self.c.close()
            except:
                pass

        # cleanup files
        for filename in self.cleanup_filenames:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                shutil.rmtree(filename)
        self.cleanup_filenames = []
