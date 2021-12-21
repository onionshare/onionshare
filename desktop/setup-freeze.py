#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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
import os
from cx_Freeze import setup, Executable

with open(os.path.join("..", "cli", "onionshare_cli", "resources", "version.txt")) as f:
    version = f.read().strip()

setup(
    name="onionshare",
    version=version,
    description="Securely and anonymously share files, host websites, and chat with friends using the Tor network",
    options={
        "build_exe": {
            "packages": [
                "cffi",  # required
                "engineio",  # required
                "engineio.async_drivers.gevent",  # required
                "engineio.async_drivers.gevent_uwsgi",  # required
                "eventlet",  # required
                "eventlet.wsgi",  # required
                "jinja2.ext",  # required
                "onionshare",  # required
                "onionshare_cli",  # required
                # "engineio.async_drivers.aiohttp",
                # "engineio.async_drivers.sanic",
                # "engineio.async_drivers.threading",
                # "engineio.async_drivers.tornado",
                # "engineio.asyncio_client",
                # "eventlet.green.OpenSSL.SSL",
                # "eventlet.green.OpenSSL.crypto",
                # "eventlet.green.OpenSSL.tsafe",
                # "eventlet.green.OpenSSL.version",
                # "eventlet.green.thread",
                # "eventlet.greenio.base",
                # "eventlet.hubs.hub",
                # "eventlet.hubs.pyevent",
                # "eventlet.queue",
                # "eventlet.support.pylib",
                # "eventlet.support.stacklesspypys",
                # "eventlet.support.stacklesss",
                # "eventlet.websocket",
                # "eventlet.zipkin._thrift.zipkinCore.constants",
                # "eventlet.zipkin._thrift.zipkinCore.ttypes",
                # "eventlet.zipkin.client",
                # "flask.cli",
                # "flask.signals",
                # "flask_socketio",
                # "itsdangerous._json",
                # "jinja2._compat",
                # "jinja2.utils",
                # "requests.compat",
                # "requests.packages",
                # "requests.utils",
                # "six",
                # "socketio.asyncio_aiopika_manager",
                # "socketio.asyncio_redis_manager",
                # "socketio.kafka_manager",
                # "socketio.kombu_manager",
                # "socketio.msgpack_packet",
                # "socketio.redis_manager",
                # "urllib.request",
                # "urllib3._collections",
                # "urllib3.connection",
                # "urllib3.connectionpool",
                # "urllib3.contrib.pyopenssl",
                # "urllib3.exceptions",
                # "urllib3.packages.six",
                # "urllib3.packages.ssl_match_hostname",
                # "urllib3.poolmanager",
                # "urllib3.request",
                # "urllib3.response",
                # "urllib3.util.queue",
                # "urllib3.util.request",
                # "urllib3.util.response",
                # "werkzeug._compat",
                # "werkzeug._reloader",
                # "werkzeug.debug.tbtools",
                # "werkzeug.http",
                # "werkzeug.serving",
                # "werkzeug.test",
                # "werkzeug.utils",
                # "werkzeug.wrappers.json",
            ],
            "excludes": ["test", "tkinter"],
            "include_files": [("..\LICENSE", "LICENSE")],
            "include_msvcr": True,
        }
    },
    executables=[
        Executable(
            "package/onionshare.py",
            # base="Win32GUI",
            base=None,
            icon=os.path.join("onionshare", "resources", "onionshare.ico"),
        ),
        Executable(
            "package/onionshare-cli.py",
            base=None,
            icon=os.path.join("onionshare", "resources", "onionshare.ico"),
        ),
    ],
)
