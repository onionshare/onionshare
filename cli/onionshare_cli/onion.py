# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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

from .censorship import CensorshipCircumvention
from .meek import Meek
from stem.control import Controller
from stem import ProtocolError, SocketClosed
from stem.connection import MissingPassword, UnreadableCookieFile, AuthenticationFailure
import base64
import nacl.public
import os
import psutil
import shlex
import subprocess
import tempfile
import time
import traceback

from distutils.version import LooseVersion as Version


class TorErrorAutomatic(Exception):
    """
    OnionShare is failing to connect and authenticate to the Tor controller,
    using automatic settings that should work with Tor Browser.
    """


class TorErrorInvalidSetting(Exception):
    """
    This exception is raised if the settings just don't make sense.
    """


class TorErrorSocketPort(Exception):
    """
    OnionShare can't connect to the Tor controller using the supplied address and port.
    """


class TorErrorSocketFile(Exception):
    """
    OnionShare can't connect to the Tor controller using the supplied socket file.
    """


class TorErrorMissingPassword(Exception):
    """
    OnionShare connected to the Tor controller, but it requires a password.
    """


class TorErrorUnreadableCookieFile(Exception):
    """
    OnionShare connected to the Tor controller, but your user does not have permission
    to access the cookie file.
    """


class TorErrorAuthError(Exception):
    """
    OnionShare connected to the address and port, but can't authenticate. It's possible
    that a Tor controller isn't listening on this port.
    """


class TorErrorProtocolError(Exception):
    """
    This exception is raised if onionshare connects to the Tor controller, but it
    isn't acting like a Tor controller (such as in Whonix).
    """


class TorTooOldEphemeral(Exception):
    """
    This exception is raised if the version of tor doesn't support ephemeral onion services
    """


class TorTooOldStealth(Exception):
    """
    This exception is raised if the version of tor doesn't support stealth onion services
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


class PortNotAvailable(Exception):
    """
    There are no available ports for OnionShare to use, which really shouldn't ever happen
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

    def __init__(self, common, use_tmp_dir=False, get_tor_paths=None):
        self.common = common
        self.common.log("Onion", "__init__")

        self.use_tmp_dir = use_tmp_dir

        # Set the path of the tor binary, for bundled tor
        if not get_tor_paths:
            get_tor_paths = self.common.get_tor_paths
        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
            self.snowflake_file_path,
            self.meek_client_file_path,
        ) = get_tor_paths()

        # The tor process
        self.tor_proc = None

        # The Tor controller
        self.c = None

        # Start out not connected to Tor
        self.connected_to_tor = False

        # Assigned later if we are using stealth mode
        self.auth_string = None

        # Keep track of onions where it's important to gracefully close to prevent truncated downloads
        self.graceful_close_onions = []

    def key_str(self, key):
        """
        Returns a base32 decoded string of a key.
        """
        # bytes to base 32
        key_bytes = bytes(key)
        key_b32 = base64.b32encode(key_bytes)
        # strip trailing ====
        assert key_b32[-4:] == b"===="
        key_b32 = key_b32[:-4]
        # change from b'ASDF' to ASDF
        s = key_b32.decode("utf-8")
        return s

    def connect(
        self,
        custom_settings=None,
        config=None,
        tor_status_update_func=None,
        connect_timeout=120,
        local_only=False,
    ):
        if local_only:
            self.common.log(
                "Onion", "connect", "--local-only, so skip trying to connect"
            )
            return

        # Either use settings that are passed in, or use them from common
        if custom_settings:
            self.settings = custom_settings
        elif config:
            self.common.load_settings(config)
            self.settings = self.common.settings
        else:
            self.common.load_settings()
            self.settings = self.common.settings

        self.common.log(
            "Onion",
            "connect",
            f"connection_type={self.settings.get('connection_type')}",
        )

        # The Tor controller
        self.c = None

        if self.settings.get("connection_type") == "bundled":
            # Create a torrc for this session
            if self.use_tmp_dir:
                self.tor_data_directory = tempfile.TemporaryDirectory(
                    dir=self.common.build_tmp_dir()
                )
                self.tor_data_directory_name = self.tor_data_directory.name
            else:
                self.tor_data_directory_name = self.common.build_tor_dir()
            self.common.log(
                "Onion",
                "connect",
                f"tor_data_directory_name={self.tor_data_directory_name}",
            )

            # Create the torrc
            with open(self.common.get_resource_path("torrc_template")) as f:
                torrc_template = f.read()
            self.tor_cookie_auth_file = os.path.join(
                self.tor_data_directory_name, "cookie"
            )
            try:
                self.tor_socks_port = self.common.get_available_port(1000, 65535)
            except Exception:
                print("OnionShare port not available")
                raise PortNotAvailable()
            self.tor_torrc = os.path.join(self.tor_data_directory_name, "torrc")

            # If there is an existing OnionShare tor process, kill it
            for proc in psutil.process_iter(["pid", "name", "username"]):
                try:
                    cmdline = proc.cmdline()
                    if (
                        cmdline[0] == self.tor_path
                        and cmdline[1] == "-f"
                        and cmdline[2] == self.tor_torrc
                    ):
                        self.common.log(
                            "Onion", "connect", "found a stale tor process, killing it"
                        )
                        proc.terminate()
                        proc.wait()
                        break
                except Exception:
                    pass

            if self.common.platform == "Windows" or self.common.platform == "Darwin":
                # Windows doesn't support unix sockets, so it must use a network port.
                # macOS can't use unix sockets either because socket filenames are limited to
                # 100 chars, and the macOS sandbox forces us to put the socket file in a place
                # with a really long path.
                torrc_template += "ControlPort {{control_port}}\n"
                try:
                    self.tor_control_port = self.common.get_available_port(1000, 65535)
                except Exception:
                    print("OnionShare port not available")
                    raise PortNotAvailable()
                self.tor_control_socket = None
            else:
                # Linux and BSD can use unix sockets
                torrc_template += "ControlSocket {{control_socket}}\n"
                self.tor_control_port = None
                self.tor_control_socket = os.path.join(
                    self.tor_data_directory_name, "control_socket"
                )

            torrc_template = torrc_template.replace(
                "{{data_directory}}", self.tor_data_directory_name
            )
            torrc_template = torrc_template.replace(
                "{{control_port}}", str(self.tor_control_port)
            )
            torrc_template = torrc_template.replace(
                "{{control_socket}}", str(self.tor_control_socket)
            )
            torrc_template = torrc_template.replace(
                "{{cookie_auth_file}}", self.tor_cookie_auth_file
            )
            torrc_template = torrc_template.replace(
                "{{geo_ip_file}}", self.tor_geo_ip_file_path
            )
            torrc_template = torrc_template.replace(
                "{{geo_ipv6_file}}", self.tor_geo_ipv6_file_path
            )
            torrc_template = torrc_template.replace(
                "{{socks_port}}", str(self.tor_socks_port)
            )
            torrc_template = torrc_template.replace(
                "{{obfs4proxy_path}}", str(self.obfs4proxy_file_path)
            )
            torrc_template = torrc_template.replace(
                "{{snowflake_path}}", str(self.snowflake_file_path)
            )

            with open(self.tor_torrc, "w") as f:
                self.common.log("Onion", "connect", "Writing torrc template file")
                f.write(torrc_template)

                # Bridge support
                if self.settings.get("bridges_enabled"):
                    f.write("\nUseBridges 1\n")
                    if self.settings.get("bridges_type") == "built-in":
                        use_torrc_bridge_templates = False
                        builtin_bridge_type = self.settings.get("bridges_builtin_pt")
                        # Use built-inbridges stored in settings, if they are there already.
                        # They are probably newer than that of our hardcoded copies.
                        if self.settings.get("bridges_builtin"):
                            try:
                                for line in self.settings.get("bridges_builtin")[
                                    builtin_bridge_type
                                ]:
                                    if line.strip() != "":
                                        f.write(f"Bridge {line}\n")
                                self.common.log(
                                    "Onion",
                                    "connect",
                                    "Wrote in the built-in bridges from OnionShare settings",
                                )
                            except KeyError:
                                # Somehow we had built-in bridges in our settings, but
                                # not for this bridge type. Fall back to using the hard-
                                # coded templates.
                                use_torrc_bridge_templates = True
                        else:
                            use_torrc_bridge_templates = True
                        if use_torrc_bridge_templates:
                            if builtin_bridge_type == "obfs4":
                                with open(
                                    self.common.get_resource_path(
                                        "torrc_template-obfs4"
                                    )
                                ) as o:
                                    f.write(o.read())
                            elif builtin_bridge_type == "meek-azure":
                                with open(
                                    self.common.get_resource_path(
                                        "torrc_template-meek_lite_azure"
                                    )
                                ) as o:
                                    f.write(o.read())
                            elif builtin_bridge_type == "snowflake":
                                with open(
                                    self.common.get_resource_path(
                                        "torrc_template-snowflake"
                                    )
                                ) as o:
                                    f.write(o.read())
                            self.common.log(
                                "Onion",
                                "connect",
                                "Wrote in the built-in bridges from torrc templates",
                            )
                    elif self.settings.get("bridges_type") == "moat":
                        for line in self.settings.get("bridges_moat").split("\n"):
                            if line.strip() != "":
                                f.write(f"Bridge {line}\n")

                    elif self.settings.get("bridges_type") == "custom":
                        for line in self.settings.get("bridges_custom").split("\n"):
                            if line.strip() != "":
                                f.write(f"Bridge {line}\n")

            # Execute a tor subprocess
            self.common.log("Onion", "connect", f"starting {self.tor_path} subprocess")
            start_ts = time.time()
            if self.common.platform == "Windows":
                # In Windows, hide console window when opening tor.exe subprocess
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.tor_proc = subprocess.Popen(
                    [self.tor_path, "-f", self.tor_torrc],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                )
            else:
                if self.common.is_snapcraft():
                    env = None
                else:
                    env = {"LD_LIBRARY_PATH": os.path.dirname(self.tor_path)}

                self.tor_proc = subprocess.Popen(
                    [self.tor_path, "-f", self.tor_torrc],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )

            # Wait for the tor controller to start
            self.common.log("Onion", "connect", f"tor pid: {self.tor_proc.pid}")
            time.sleep(2)

            return_code = self.tor_proc.poll()
            if return_code != None:
                self.common.log("Onion", "connect", f"tor process has terminated early: {return_code}")

            # Connect to the controller
            self.common.log("Onion", "connect", "authenticating to tor controller")
            try:
                if (
                    self.common.platform == "Windows"
                    or self.common.platform == "Darwin"
                ):
                    self.c = Controller.from_port(port=self.tor_control_port)
                    self.c.authenticate()
                else:
                    self.c = Controller.from_socket_file(path=self.tor_control_socket)
                    self.c.authenticate()
            except Exception as e:
                print("OnionShare could not connect to Tor:\n{}".format(e.args[0]))
                print(traceback.format_exc())
                raise BundledTorBroken(e.args[0])

            while True:
                try:
                    res = self.c.get_info("status/bootstrap-phase")
                except SocketClosed:
                    raise BundledTorCanceled()

                res_parts = shlex.split(res)
                progress = res_parts[2].split("=")[1]
                summary = res_parts[4].split("=")[1]

                # "\033[K" clears the rest of the line
                print(
                    f"\rConnecting to the Tor network: {progress}% - {summary}\033[K",
                    end="",
                )

                if callable(tor_status_update_func):
                    if not tor_status_update_func(progress, summary):
                        # If the dialog was canceled, stop connecting to Tor
                        self.common.log(
                            "Onion",
                            "connect",
                            "tor_status_update_func returned false, canceling connecting to Tor",
                        )
                        print()
                        return False

                if summary == "Done":
                    print("")
                    break
                time.sleep(0.2)

                # If using bridges, it might take a bit longer to connect to Tor
                if self.settings.get("bridges_enabled"):
                    # Only override timeout if a custom timeout has not been passed in
                    if connect_timeout == 120:
                        connect_timeout = 150
                if time.time() - start_ts > connect_timeout:
                    print("")
                    try:
                        self.tor_proc.terminate()
                        print(
                            "Taking too long to connect to Tor. Maybe you aren't connected to the Internet, or have an inaccurate system clock?"
                        )
                        raise BundledTorTimeout()
                    except FileNotFoundError:
                        pass

        elif self.settings.get("connection_type") == "automatic":
            # Automatically try to guess the right way to connect to Tor Browser
            automatic_error = "Could not connect to the Tor controller. Is Tor Browser (available from torproject.org) running in the background?"

            # Try connecting to control port
            found_tor = False

            # If the TOR_CONTROL_PORT environment variable is set, use that
            env_port = os.environ.get("TOR_CONTROL_PORT")
            if env_port:
                try:
                    self.c = Controller.from_port(port=int(env_port))
                    found_tor = True
                except Exception:
                    pass

            else:
                # Otherwise, try default ports for Tor Browser, Tor Messenger, and system tor
                try:
                    ports = [9151, 9153, 9051]
                    for port in ports:
                        self.c = Controller.from_port(port=port)
                        found_tor = True
                except Exception:
                    pass

                # If this still didn't work, try guessing the default socket file path
                socket_file_path = ""
                if not found_tor:
                    try:
                        if self.common.platform == "Darwin":
                            socket_file_path = os.path.expanduser(
                                "~/Library/Application Support/TorBrowser-Data/Tor/control.socket"
                            )

                        self.c = Controller.from_socket_file(path=socket_file_path)
                        found_tor = True
                    except Exception:
                        pass

            # If connecting to default control ports failed, so let's try
            # guessing the socket file name next
            if not found_tor:
                try:
                    if self.common.platform == "Linux" or self.common.platform == "BSD":
                        socket_file_path = (
                            f"/run/user/{os.geteuid()}/Tor/control.socket"
                        )
                    elif self.common.platform == "Darwin":
                        socket_file_path = (
                            f"/run/user/{os.geteuid()}/Tor/control.socket"
                        )
                    elif self.common.platform == "Windows":
                        # Windows doesn't support unix sockets
                        print(automatic_error)
                        raise TorErrorAutomatic()

                    self.c = Controller.from_socket_file(path=socket_file_path)

                except Exception:
                    print(automatic_error)
                    raise TorErrorAutomatic()

            # Try authenticating
            try:
                self.c.authenticate()
            except Exception:
                print(automatic_error)
                raise TorErrorAutomatic()

        else:
            # Use specific settings to connect to tor
            invalid_settings_error = "Can't connect to Tor controller because your settings don't make sense."

            # Try connecting
            try:
                if self.settings.get("connection_type") == "control_port":
                    self.c = Controller.from_port(
                        address=self.settings.get("control_port_address"),
                        port=self.settings.get("control_port_port"),
                    )
                elif self.settings.get("connection_type") == "socket_file":
                    self.c = Controller.from_socket_file(
                        path=self.settings.get("socket_file_path")
                    )
                else:
                    print(invalid_settings_error)
                    raise TorErrorInvalidSetting()

            except Exception:
                if self.settings.get("connection_type") == "control_port":
                    print(
                        "Can't connect to the Tor controller at {}:{}.".format(
                            self.settings.get("control_port_address"),
                            self.settings.get("control_port_port"),
                        )
                    )
                    raise TorErrorSocketPort(
                        self.settings.get("control_port_address"),
                        self.settings.get("control_port_port"),
                    )
                print(
                    "Can't connect to the Tor controller using socket file {}.".format(
                        self.settings.get("socket_file_path")
                    )
                )
                raise TorErrorSocketFile(self.settings.get("socket_file_path"))

            # Try authenticating
            try:
                if self.settings.get("auth_type") == "no_auth":
                    self.c.authenticate()
                elif self.settings.get("auth_type") == "password":
                    self.c.authenticate(self.settings.get("auth_password"))
                else:
                    print(invalid_settings_error)
                    raise TorErrorInvalidSetting()

            except MissingPassword:
                print(
                    "Connected to Tor controller, but it requires a password to authenticate."
                )
                raise TorErrorMissingPassword()
            except UnreadableCookieFile:
                print(
                    "Connected to the Tor controller, but password may be wrong, or your user is not permitted to read the cookie file."
                )
                raise TorErrorUnreadableCookieFile()
            except AuthenticationFailure:
                print(
                    "Connected to {}:{}, but can't authenticate. Maybe this isn't a Tor controller?".format(
                        self.settings.get("control_port_address"),
                        self.settings.get("control_port_port"),
                    )
                )
                raise TorErrorAuthError(
                    self.settings.get("control_port_address"),
                    self.settings.get("control_port_port"),
                )

        # If we made it this far, we should be connected to Tor
        self.connected_to_tor = True

        # Get the tor version
        self.tor_version = self.c.get_version().version_str
        self.common.log("Onion", "connect", f"Connected to tor {self.tor_version}")

        # Do the versions of stem and tor that I'm using support ephemeral onion services?
        list_ephemeral_hidden_services = getattr(
            self.c, "list_ephemeral_hidden_services", None
        )
        self.supports_ephemeral = (
            callable(list_ephemeral_hidden_services) and self.tor_version >= "0.2.7.1"
        )

        # Do the versions of stem and tor that I'm using support v3 stealth onion services?
        try:
            res = self.c.create_ephemeral_hidden_service(
                {1: 1},
                basic_auth=None,
                await_publication=False,
                key_type="NEW",
                key_content="ED25519-V3",
                client_auth_v3="E2GOT5LTUTP3OAMRCRXO4GSH6VKJEUOXZQUC336SRKAHTTT5OVSA",
            )
            tmp_service_id = res.service_id
            self.c.remove_ephemeral_hidden_service(tmp_service_id)
            self.supports_stealth = True
        except Exception:
            # ephemeral stealth onion services are not supported
            self.supports_stealth = False

        # Does this version of Tor support next-gen ('v3') onions?
        # Note, this is the version of Tor where this bug was fixed:
        # https://trac.torproject.org/projects/tor/ticket/28619
        self.supports_v3_onions = self.tor_version >= Version("0.3.5.7")

        # Now that we are connected to Tor, if we are using built-in bridges,
        # update them with the latest copy available from the Tor API
        if (
            self.settings.get("bridges_enabled")
            and self.settings.get("bridges_type") == "built-in"
        ):
            self.update_builtin_bridges()

    def is_authenticated(self):
        """
        Returns True if the Tor connection is still working, or False otherwise.
        """
        if self.c is not None:
            return self.c.is_authenticated()
        else:
            return False

    def start_onion_service(self, mode, mode_settings, port, await_publication):
        """
        Start a onion service on port 80, pointing to the given port, and
        return the onion hostname.
        """
        self.common.log("Onion", "start_onion_service", f"port={port}")

        if not self.supports_ephemeral:
            print(
                "Your version of Tor is too old, ephemeral onion services are not supported"
            )
            raise TorTooOldEphemeral()

        if mode_settings.get("onion", "private_key"):
            key_content = mode_settings.get("onion", "private_key")
            key_type = "ED25519-V3"
        else:
            key_content = "ED25519-V3"
            key_type = "NEW"

        debug_message = f"key_type={key_type}"
        if key_type == "NEW":
            debug_message += f", key_content={key_content}"
        self.common.log("Onion", "start_onion_service", debug_message)

        if mode_settings.get("general", "public"):
            client_auth_priv_key = None
            client_auth_pub_key = None
        else:
            if not self.supports_stealth:
                print(
                    "Your version of Tor is too old, stealth onion services are not supported"
                )
                raise TorTooOldStealth()
            else:
                if key_type == "NEW" or not mode_settings.get(
                    "onion", "client_auth_priv_key"
                ):
                    # Generate a new key pair for Client Auth on new onions, or if
                    # it's a persistent onion but for some reason we don't them
                    client_auth_priv_key_raw = nacl.public.PrivateKey.generate()
                    client_auth_priv_key = self.key_str(client_auth_priv_key_raw)
                    client_auth_pub_key = self.key_str(
                        client_auth_priv_key_raw.public_key
                    )
                else:
                    # These should have been saved in settings from the previous run of a persistent onion
                    client_auth_priv_key = mode_settings.get(
                        "onion", "client_auth_priv_key"
                    )
                    client_auth_pub_key = mode_settings.get(
                        "onion", "client_auth_pub_key"
                    )

        try:
            if not self.supports_stealth:
                res = self.c.create_ephemeral_hidden_service(
                    {80: port},
                    await_publication=await_publication,
                    basic_auth=None,
                    key_type=key_type,
                    key_content=key_content,
                )
            else:
                res = self.c.create_ephemeral_hidden_service(
                    {80: port},
                    await_publication=await_publication,
                    basic_auth=None,
                    key_type=key_type,
                    key_content=key_content,
                    client_auth_v3=client_auth_pub_key,
                )

        except ProtocolError as e:
            print("Tor error: {}".format(e.args[0]))
            raise TorErrorProtocolError(e.args[0])

        onion_host = res.service_id + ".onion"

        # Gracefully close share mode rendezvous circuits
        if mode == "share":
            self.graceful_close_onions.append(res.service_id)

        # Save the service_id
        mode_settings.set("general", "service_id", res.service_id)

        # Save the private key and hidservauth string
        if not mode_settings.get("onion", "private_key"):
            mode_settings.set("onion", "private_key", res.private_key)

        # If using V3 onions and Client Auth, save both the private and public key
        # because we need to send the public key to ADD_ONION (if we restart this
        # same share at a later date), and the private key to the other user for
        # their Tor Browser.
        if not mode_settings.get("general", "public"):
            mode_settings.set("onion", "client_auth_priv_key", client_auth_priv_key)
            mode_settings.set("onion", "client_auth_pub_key", client_auth_pub_key)
            # If we were pasting the client auth directly into the filesystem behind a Tor client,
            # it would need to be in the format below. However, let's just set the private key
            # by itself, as this can be pasted directly into Tor Browser, which is likely to
            # be the most common use case.
            # self.auth_string = f"{onion_host}:x25519:{client_auth_priv_key}"
            self.auth_string = client_auth_priv_key

        return onion_host

    def stop_onion_service(self, mode_settings):
        """
        Stop a specific onion service
        """
        onion_host = mode_settings.get("general", "service_id")
        if onion_host:
            self.common.log("Onion", "stop_onion_service", f"onion host: {onion_host}")
            try:
                self.c.remove_ephemeral_hidden_service(
                    mode_settings.get("general", "service_id")
                )
            except Exception:
                self.common.log(
                    "Onion", "stop_onion_service", f"failed to remove {onion_host}"
                )

    def cleanup(self, stop_tor=True, wait=True):
        """
        Stop onion services that were created earlier. If there's a tor subprocess running, kill it.
        """
        self.common.log("Onion", "cleanup")

        # Cleanup the ephemeral onion services, if we have any
        try:
            onions = self.c.list_ephemeral_hidden_services()
            for service_id in onions:
                onion_host = f"{service_id}.onion"
                try:
                    self.common.log(
                        "Onion", "cleanup", f"trying to remove onion {onion_host}"
                    )
                    self.c.remove_ephemeral_hidden_service(service_id)
                except Exception:
                    self.common.log(
                        "Onion", "cleanup", f"failed to remove onion {onion_host}"
                    )
                    pass
        except Exception:
            pass

        if stop_tor:
            # Stop tor process
            if self.tor_proc:
                if wait:
                    # Wait for Tor rendezvous circuits to close
                    # Catch exceptions to prevent crash on Ctrl-C
                    try:
                        rendezvous_circuit_ids = []
                        for c in self.c.get_circuits():
                            if (
                                c.purpose == "HS_SERVICE_REND"
                                and c.rend_query in self.graceful_close_onions
                            ):
                                rendezvous_circuit_ids.append(c.id)

                        symbols = list("\\|/-")
                        symbols_i = 0

                        while True:
                            num_rend_circuits = 0
                            for c in self.c.get_circuits():
                                if c.id in rendezvous_circuit_ids:
                                    num_rend_circuits += 1

                            if num_rend_circuits == 0:
                                print(
                                    "\rTor rendezvous circuits have closed" + " " * 20
                                )
                                break

                            if num_rend_circuits == 1:
                                circuits = "circuit"
                            else:
                                circuits = "circuits"
                            print(
                                f"\rWaiting for {num_rend_circuits} Tor rendezvous {circuits} to close {symbols[symbols_i]} ",
                                end="",
                            )
                            symbols_i = (symbols_i + 1) % len(symbols)
                            time.sleep(1)
                    except Exception:
                        pass

                self.tor_proc.terminate()
                time.sleep(0.2)
                if self.tor_proc.poll() is None:
                    self.common.log(
                        "Onion",
                        "cleanup",
                        "Tried to terminate tor process but it's still running",
                    )
                    try:
                        self.tor_proc.kill()
                        time.sleep(0.2)
                        if self.tor_proc.poll() is None:
                            self.common.log(
                                "Onion",
                                "cleanup",
                                "Tried to kill tor process but it's still running",
                            )
                    except Exception:
                        self.common.log(
                            "Onion", "cleanup", "Exception while killing tor process"
                        )
                self.tor_proc = None

            # Reset other Onion settings
            self.connected_to_tor = False

            try:
                # Delete the temporary tor data directory
                if self.use_tmp_dir:
                    self.tor_data_directory.cleanup()
            except Exception:
                pass

    def get_tor_socks_port(self):
        """
        Returns a (address, port) tuple for the Tor SOCKS port
        """
        self.common.log("Onion", "get_tor_socks_port")

        if self.settings.get("connection_type") == "bundled":
            return ("127.0.0.1", self.tor_socks_port)
        elif self.settings.get("connection_type") == "automatic":
            return ("127.0.0.1", 9150)
        else:
            return (self.settings.get("socks_address"), self.settings.get("socks_port"))

    def update_builtin_bridges(self):
        """
        Use the CensorshipCircumvention API to fetch the latest built-in bridges
        and update them in settings.
        """
        builtin_bridges = False
        meek = None
        # Try obtaining bridges over Tor, if we're connected to it.
        if self.is_authenticated:
            self.common.log(
                "Onion",
                "update_builtin_bridges",
                "Updating the built-in bridges. Trying over Tor first",
            )
            self.censorship_circumvention = CensorshipCircumvention(
                self.common, None, self
            )
            builtin_bridges = self.censorship_circumvention.request_builtin_bridges()

        if not builtin_bridges:
            # Tor was not running or it failed to hit the Tor API.
            # Fall back to using Meek (domain-fronting).
            self.common.log(
                "Onion",
                "update_builtin_bridges",
                "Updating the built-in bridges. Trying via Meek (no Tor)",
            )
            meek = Meek(self.common)
            meek.start()
            self.censorship_circumvention = CensorshipCircumvention(
                self.common, meek, None
            )
            builtin_bridges = self.censorship_circumvention.request_builtin_bridges()
            meek.cleanup()

        if builtin_bridges:
            # If we got to this point, we have bridges
            self.common.log(
                "Onion",
                "update_builtin_bridges",
                f"Obtained bridges: {builtin_bridges}",
            )
            # Save the new settings
            self.settings.set("bridges_builtin", builtin_bridges)
            self.settings.save()
        else:
            self.common.log(
                "Onion", "update_builtin_bridges", "Error getting built-in bridges"
            )
            return False
