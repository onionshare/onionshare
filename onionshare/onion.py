# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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
from stem import ProtocolError
from stem.connection import MissingPassword, UnreadableCookieFile, AuthenticationFailure
import os, sys, tempfile, shutil, urllib, platform

from . import socks
from . import helpers, strings
from .settings import Settings

class TorErrorAutomatic(Exception):
    """
    OnionShare is failing to connect and authenticate to the Tor controller,
    using automatic settings that should work with Tor Browser.
    """
    pass

class TorErrorInvalidSetting(Exception):
    """
    This exception is raised if the settings just don't make sense.
    """
    pass

class TorErrorSocketPort(Exception):
    """
    OnionShare can't connect to the Tor controller using the supplied address and port.
    """
    pass

class TorErrorSocketFile(Exception):
    """
    OnionShare can't connect to the Tor controller using the supplied socket file.
    """
    pass

class TorErrorMissingPassword(Exception):
    """
    OnionShare connected to the Tor controller, but it requires a password.
    """
    pass

class TorErrorUnreadableCookieFile(Exception):
    """
    OnionShare connected to the Tor controller, but your user does not have permission
    to access the cookie file.
    """
    pass

class TorErrorAuthError(Exception):
    """
    OnionShare connected to the address and port, but can't authenticate. It's possible
    that a Tor controller isn't listening on this port.
    """
    pass

class TorErrorProtocolError(Exception):
    """
    This exception is raised if onionshare connects to the Tor controller, but it
    isn't acting like a Tor controller (such as in Whonix).
    """
    pass

class TorTooOld(Exception):
    """
    This exception is raised if onionshare needs to use a feature of Tor or stem
    (like stealth ephemeral onion services) but the version you have installed
    is too old.
    """
    pass

class BundledTorNotSupported(Exception):
    """
    This exception is raised if onionshare is set to use the bundled Tor binary,
    but it's not supported on that platform, or in dev mode.
    """

class Onion(object):
    """
    Onion is an abstraction layer for connecting to the Tor control port and
    creating onion services. OnionShare supports creating onion services by
    connecting to the Tor controller and using ADD_ONION, DEL_ONION.
    """
    def __init__(self, stealth=False, settings=False):
        self.stealth = stealth
        self.service_id = None

        # Either use settings that are passed in, or load them from disk
        if settings:
            self.settings = settings
        else:
            self.settings = Settings()
            self.settings.load()

        # Try to connect to Tor
        self.c = None

        if self.settings.get('connection_type') == 'bundled':
            dev_mode = getattr(sys, 'onionshare_dev_mode', False)
            p = platform.system()

            if (p != 'Windows' and p != 'Darwin') or dev_mode:
                raise BundledTorNotSupported(strings._('settings_error_bundled_tor_not_supported'))

            # TODO: actually implement bundled Tor

        if self.settings.get('connection_type') == 'automatic':
            # Automatically try to guess the right way to connect to Tor Browser
            p = platform.system()

            # Try connecting to control port
            found_tor = False

            # If the TOR_CONTROL_PORT environment variable is set, use that
            env_port = os.environ.get('TOR_CONTROL_PORT')
            if env_port:
                try:
                    self.c = Controller.from_port(port=int(env_port))
                    found_tor = True
                except:
                    pass

            else:
                # Otherwise, try default ports for Tor Browser, Tor Messenger, and system tor
                try:
                    ports = [9151, 9153, 9051]
                    for port in ports:
                        self.c = Controller.from_port(port=port)
                        found_tor = True
                except:
                    pass

                # If this still didn't work, try guessing the default socket file path
                socket_file_path = ''
                if not found_tor:
                    try:
                        if p == 'Darwin':
                            socket_file_path = os.path.expanduser('~/Library/Application Support/TorBrowser-Data/Tor/control.socket')

                        self.c = Controller.from_socket_file(path=socket_file_path)
                        found_tor = True
                    except:
                        pass

            # If connecting to default control ports failed, so let's try
            # guessing the socket file name next
            if not found_tor:
                try:
                    if p == 'Linux':
                        socket_file_path = '/run/user/{}/Tor/control.socket'.format(os.geteuid())
                    elif p == 'Darwin':
                        # TODO: figure out the unix socket path in OS X
                        socket_file_path = '/run/user/{}/Tor/control.socket'.format(os.geteuid())
                    elif p == 'Windows':
                        # Windows doesn't support unix sockets
                        raise TorErrorAutomatic(strings._('settings_error_automatic'))

                    self.c = Controller.from_socket_file(path=socket_file_path)

                except:
                    raise TorErrorAutomatic(strings._('settings_error_automatic'))

            # Try authenticating
            try:
                self.c.authenticate()
            except:
                raise TorErrorAutomatic(strings._('settings_error_automatic'))

        else:
            # Use specific settings to connect to tor

            # Try connecting
            try:
                if self.settings.get('connection_type') == 'control_port':
                    self.c = Controller.from_port(address=self.settings.get('control_port_address'), port=self.settings.get('control_port_port'))
                elif self.settings.get('connection_type') == 'socket_file':
                    self.c = Controller.from_socket_file(path=self.settings.get('socket_file_path'))
                else:
                    raise TorErrorInvalidSetting(strings._("settings_error_unknown"))

            except:
                if self.settings.get('connection_type') == 'control_port':
                    raise TorErrorSocketPort(strings._("settings_error_socket_port").format(self.settings.get('control_port_address'), self.settings.get('control_port_port')))
                else:
                    raise TorErrorSocketFile(strings._("settings_error_socket_file").format(self.settings.get('socket_file_path')))


            # Try authenticating
            try:
                if self.settings.get('auth_type') == 'no_auth':
                    self.c.authenticate()
                elif self.settings.get('auth_type') == 'password':
                    self.c.authenticate(self.settings.get('auth_password'))
                else:
                    raise TorErrorInvalidSetting(strings._("settings_error_unknown"))

            except MissingPassword:
                raise TorErrorMissingPassword(strings._('settings_error_missing_password'))
            except UnreadableCookieFile:
                raise TorErrorUnreadableCookieFile(strings._('settings_error_unreadable_cookie_file'))
            except AuthenticationFailure:
                raise TorErrorAuthError(strings._('settings_error_auth').format(self.settings.get('control_port_address'), self.settings.get('control_port_port')))

        # Get the tor version
        self.tor_version = self.c.get_version().version_str

        # Do the versions of stem and tor that I'm using support ephemeral onion services?
        list_ephemeral_hidden_services = getattr(self.c, "list_ephemeral_hidden_services", None)
        self.supports_ephemeral = callable(list_ephemeral_hidden_services) and self.tor_version >= '0.2.7.1'

        # Do the versions of stem and tor that I'm using support stealth onion services?
        try:
            res = self.c.create_ephemeral_hidden_service({1:1}, basic_auth={'onionshare':None}, await_publication=False)
            tmp_service_id = res.content()[0][2].split('=')[1]
            self.c.remove_ephemeral_hidden_service(tmp_service_id)
            self.supports_stealth = True
        except:
            # ephemeral stealth onion services are not supported
            self.supports_stealth = False

    def start(self, port):
        """
        Start a onion service on port 80, pointing to the given port, and
        return the onion hostname.
        """
        self.auth_string = None
        if not self.supports_ephemeral:
            raise TorTooOld(strings._('error_ephemeral_not_supported'))
        if self.stealth and not self.supports_stealth:
            raise TorTooOld(strings._('error_stealth_not_supported'))

        print(strings._("config_onion_service").format(int(port)))
        print(strings._('using_ephemeral'))

        if self.stealth:
            basic_auth = {'onionshare':None}
        else:
            basic_auth = None

        try:
            if basic_auth != None :
                res = self.c.create_ephemeral_hidden_service({ 80: port }, await_publication=True, basic_auth=basic_auth)
            else :
                # if the stem interface is older than 1.5.0, basic_auth isn't a valid keyword arg
                res = self.c.create_ephemeral_hidden_service({ 80: port }, await_publication=True)

        except ProtocolError:
            raise TorErrorProtocolError(strings._('error_tor_protocol_error'))

        self.service_id = res.content()[0][2].split('=')[1]
        onion_host = self.service_id + '.onion'

        if self.stealth:
            auth_cookie = res.content()[2][2].split('=')[1].split(':')[1]
            self.auth_string = 'HidServAuth {} {}'.format(onion_host, auth_cookie)

        return onion_host

    def cleanup(self):
        """
        Stop onion services that were created earlier.
        """
        # cleanup the ephemeral onion service
        if self.service_id:
            try:
                self.c.remove_ephemeral_hidden_service(self.service_id)
            except:
                pass
            self.service_id = None
