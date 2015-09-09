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
import os, tempfile, shutil

import helpers, strings

class NoTor(Exception):
    pass

class HSDirError(Exception):
    pass

class HS(object):
    def __init__(self, transparent_torification=False):
        self.transparent_torification = transparent_torification

        # files and dirs to delete on shutdown
        self.cleanup_filenames = []

        # connect to the tor controlport
        self.c = None
        ports = [9051, 9151]
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
        print strings._("connecting_ctrlport").format(int(port))
        if self.supports_ephemeral:
            print strings._('using_ephemeral')
            res = self.c.create_ephemeral_hidden_service({ 80: port }, await_publication = True)
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

            hidserv_dir = tempfile.mkdtemp(dir=path)
            self.cleanup_filenames.append(hidserv_dir)

            # set up hidden service
            hsdic = self.c.get_conf_map('HiddenServiceOptions') or {
                'HiddenServiceDir': [], 'HiddenServicePort': []
            }
            if hidserv_dir in hsdic.get('HiddenServiceDir', []):
                # Maybe a stale service with the wrong local port
                dropme = hsdic['HiddenServiceDir'].index(hidserv_dir)
                del hsdic['HiddenServiceDir'][dropme]
                del hsdic['HiddenServicePort'][dropme]
            hsdic['HiddenServiceDir'] = hsdic.get('HiddenServiceDir', [])+[hidserv_dir]
            hsdic['HiddenServicePort'] = hsdic.get('HiddenServicePort', [])+[
                '80 127.0.0.1:{0:d}'.format(port)]

            self.c.set_options(self._hsdic2list(hsdic))

            # figure out the .onion hostname
            hostname_file = '{0:s}/hostname'.format(hidserv_dir)
            onion_host = open(hostname_file, 'r').read().strip()
            return onion_host

    def cleanup(self):
        if self.supports_ephemeral:
            # todo: cleanup the ephemeral hidden service
            pass
        else:
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
                        self.controller.set_options(self._hsdic2list(hsdic))
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

    def _hsdic2list(self, dic):
        """Convert what we get from get_conf_map to what we need for set_options"""
        return [
            pair for pairs in [
                [('HiddenServiceDir', vals[0]), ('HiddenServicePort', vals[1])]
                for vals in zip(dic.get('HiddenServiceDir', []), dic.get('HiddenServicePort', []))
            ] for pair in pairs
        ]
