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
from stem import ProtocolError, SocketClosed
from stem.connection import MissingPassword, UnreadableCookieFile, AuthenticationFailure
import os, sys, tempfile, shutil, urllib, platform, subprocess, time, shlex

from . import socks
from . import common, strings
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

class BundledTorTimeout(Exception):
    """
    This exception is raised if onionshare is set to use the bundled Tor binary,
    but Tor doesn't finish connecting promptly.
    """

class BundledTorCanceled(Exception):
    """
    This exception is raised if onionshare is set to use the bundled Tor binary,
    and the user cancels connecting to Tor
    """

class BundledTorBroken(Exception):
    """
    This exception is raised if onionshare is set to use the bundled Tor binary,
    but the process seems to fail to run.
    """

class Onion(object):
    """
    Onion is an abstraction layer for connecting to the Tor control port and
    creating onion services. OnionShare supports creating onion services by
    connecting to the Tor controller and using ADD_ONION, DEL_ONION.

    stealth: Should the onion service be stealth?

    settings: A Settings object. If it's not passed in, load from disk.

    bundled_connection_func: If the tor connection type is bundled, optionally
    call this function and pass in a status string while connecting to tor. This
    is necessary for status updates to reach the GUI.
    """
    def __init__(self):
        common.log('Onion', '__init__')

        self.stealth = False
        self.service_id = None

        self.system = platform.system()

        # Is bundled tor supported?
        if (self.system == 'Windows' or self.system == 'Darwin') and getattr(sys, 'onionshare_dev_mode', False):
            self.bundle_tor_supported = False
        else:
            self.bundle_tor_supported = True

        # Set the path of the tor binary, for bundled tor
        (self.tor_path, self.tor_geo_ip_file_path, self.tor_geo_ipv6_file_path) = common.get_tor_paths()

        # The tor process
        self.tor_proc = None

        # Start out not connected to Tor
        self.connected_to_tor = False

    def connect(self, settings=False, config=False, tor_status_update_func=None):
        common.log('Onion', 'connect')

        # Either use settings that are passed in, or load them from disk
        if settings:
            self.settings = settings
        else:
            self.settings = Settings(config)
            self.settings.load()

        # The Tor controller
        self.c = None

        if self.settings.get('connection_type') == 'bundled':
            if not self.bundle_tor_supported:
                raise BundledTorNotSupported(strings._('settings_error_bundled_tor_not_supported'))

            # Create a torrc for this session
            self.tor_data_directory = tempfile.TemporaryDirectory()

            if self.system == 'Windows':
                # Windows needs to use network ports, doesn't support unix sockets
                torrc_template = open(common.get_resource_path('torrc_template-windows')).read()
                try:
                    self.tor_control_port = common.get_available_port(1000, 65535)
                except:
                    raise OSError(strings._('no_available_port'))
                self.tor_control_socket = None
                self.tor_cookie_auth_file = os.path.join(self.tor_data_directory.name, 'cookie')
                try:
                    self.tor_socks_port = common.get_available_port(1000, 65535)
                except:
                    raise OSError(strings._('no_available_port'))
                self.tor_torrc = os.path.join(self.tor_data_directory.name, 'torrc')
            else:
                # Linux and Mac can use unix sockets
                with open(common.get_resource_path('torrc_template')) as f:
                    torrc_template = f.read()
                self.tor_control_port = None
                self.tor_control_socket = os.path.join(self.tor_data_directory.name, 'control_socket')
                self.tor_cookie_auth_file = os.path.join(self.tor_data_directory.name, 'cookie')
                try:
                    self.tor_socks_port = common.get_available_port(1000, 65535)
                except:
                    raise OSError(strings._('no_available_port'))
                self.tor_torrc = os.path.join(self.tor_data_directory.name, 'torrc')

            torrc_template = torrc_template.replace('{{data_directory}}',   self.tor_data_directory.name)
            torrc_template = torrc_template.replace('{{control_port}}',     str(self.tor_control_port))
            torrc_template = torrc_template.replace('{{control_socket}}',   str(self.tor_control_socket))
            torrc_template = torrc_template.replace('{{cookie_auth_file}}', self.tor_cookie_auth_file)
            torrc_template = torrc_template.replace('{{geo_ip_file}}',      self.tor_geo_ip_file_path)
            torrc_template = torrc_template.replace('{{geo_ipv6_file}}',    self.tor_geo_ipv6_file_path)
            torrc_template = torrc_template.replace('{{socks_port}}',       str(self.tor_socks_port))
            with open(self.tor_torrc, 'w') as f:
                f.write(torrc_template)

            # Execute a tor subprocess
            start_ts = time.time()
            if self.system == 'Windows':
                # In Windows, hide console window when opening tor.exe subprocess
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.tor_proc = subprocess.Popen([self.tor_path, '-f', self.tor_torrc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            else:
                self.tor_proc = subprocess.Popen([self.tor_path, '-f', self.tor_torrc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for the tor controller to start
            time.sleep(2)

            # Connect to the controller
            try:
                if self.system == 'Windows':
                    self.c = Controller.from_port(port=self.tor_control_port)
                    self.c.authenticate()
                else:
                    self.c = Controller.from_socket_file(path=self.tor_control_socket)
                    self.c.authenticate()
            except Exception as e:
                raise BundledTorBroken(strings._('settings_error_bundled_tor_broken', True).format(e.args[0]))

            while True:
                try:
                    res = self.c.get_info("status/bootstrap-phase")
                except SocketClosed:
                    raise BundledTorCanceled()

                res_parts = shlex.split(res)
                progress = res_parts[2].split('=')[1]
                summary = res_parts[4].split('=')[1]

                # "\033[K" clears the rest of the line
                print("{}: {}% - {}{}".format(strings._('connecting_to_tor'), progress, summary, "\033[K"), end="\r")

                if callable(tor_status_update_func):
                    if not tor_status_update_func(progress, summary):
                        # If the dialog was canceled, stop connecting to Tor
                        common.log('Onion', 'connect', 'tor_status_update_func returned false, canceling connecting to Tor')
                        print()
                        return False

                if summary == 'Done':
                    print("")
                    break
                time.sleep(0.2)

                # Timeout after 90 seconds
                if time.time() - start_ts > 90:
                    print("")
                    self.tor_proc.terminate()
                    raise BundledTorTimeout(strings._('settings_error_bundled_tor_timeout'))

        elif self.settings.get('connection_type') == 'automatic':
            # Automatically try to guess the right way to connect to Tor Browser

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
                        if self.system == 'Darwin':
                            socket_file_path = os.path.expanduser('~/Library/Application Support/TorBrowser-Data/Tor/control.socket')

                        self.c = Controller.from_socket_file(path=socket_file_path)
                        found_tor = True
                    except:
                        pass

            # If connecting to default control ports failed, so let's try
            # guessing the socket file name next
            if not found_tor:
                try:
                    if self.system == 'Linux':
                        socket_file_path = '/run/user/{}/Tor/control.socket'.format(os.geteuid())
                    elif self.system == 'Darwin':
                        socket_file_path = '/run/user/{}/Tor/control.socket'.format(os.geteuid())
                    elif self.system == 'Windows':
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

        # If we made it this far, we should be connected to Tor
        self.connected_to_tor = True

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

    def start_onion_service(self, port):
        """
        Start a onion service on port 80, pointing to the given port, and
        return the onion hostname.
        """
        common.log('Onion', 'start_onion_service')

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

        if onion_host is not None:
            return onion_host
        else:
            raise TorErrorProtocolError(strings._('error_tor_protocol_error'))

    def cleanup(self, stop_tor=True):
        """
        Stop onion services that were created earlier. If there's a tor subprocess running, kill it.
        """
        common.log('Onion', 'cleanup')

        # Cleanup the ephemeral onion service
        if self.service_id:
            try:
                self.c.remove_ephemeral_hidden_service(self.service_id)
            except:
                pass
            self.service_id = None

        if stop_tor:
            # Stop tor process
            if self.tor_proc:
                self.tor_proc.terminate()
                time.sleep(0.2)
                if not self.tor_proc.poll():
                    try:
                        self.tor_proc.kill()
                    except:
                        pass
                self.tor_proc = None

            # Reset other Onion settings
            self.connected_to_tor = False
            self.stealth = False

            try:
                # Delete the temporary tor data directory
                self.tor_data_directory.cleanup()
            except AttributeError:
                # Skip if cleanup was somehow run before connect
                pass

    def get_tor_socks_port(self):
        """
        Returns a (address, port) tuple for the Tor SOCKS port
        """
        common.log('Onion', 'get_tor_socks_port')

        if self.settings.get('connection_type') == 'bundled':
            return ('127.0.0.1', self.tor_socks_port)
        elif self.settings.get('connection_type') == 'automatic':
            return ('127.0.0.1', 9150)
        else:
            return (self.settings.get('socks_address'), self.settings.get('socks_port'))
