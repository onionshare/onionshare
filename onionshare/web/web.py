import hmac
import logging
import os
import queue
import socket
import sys
import tempfile
import requests
from distutils.version import LooseVersion as Version
from urllib.request import urlopen

import flask
from flask import Flask, request, render_template, abort, make_response, __version__ as flask_version
from flask_httpauth import HTTPBasicAuth

from .. import strings

from .share_mode import ShareModeWeb
from .receive_mode import ReceiveModeWeb, ReceiveModeWSGIMiddleware, ReceiveModeRequest
from .website_mode import WebsiteModeWeb

# Stub out flask's show_server_banner function, to avoiding showing warnings that
# are not applicable to OnionShare
def stubbed_show_server_banner(env, debug, app_import_path, eager_loading):
    pass

try:
    flask.cli.show_server_banner = stubbed_show_server_banner
except:
    pass


class Web(object):
    """
    The Web object is the OnionShare web server, powered by flask
    """
    REQUEST_LOAD = 0
    REQUEST_STARTED = 1
    REQUEST_PROGRESS = 2
    REQUEST_OTHER = 3
    REQUEST_CANCELED = 4
    REQUEST_RATE_LIMIT = 5
    REQUEST_UPLOAD_FILE_RENAMED = 6
    REQUEST_UPLOAD_SET_DIR = 7
    REQUEST_UPLOAD_FINISHED = 8
    REQUEST_UPLOAD_CANCELED = 9
    REQUEST_ERROR_DATA_DIR_CANNOT_CREATE = 10
    REQUEST_INVALID_SLUG = 11

    def __init__(self, common, is_gui, mode='share'):
        self.common = common
        self.common.log('Web', '__init__', 'is_gui={}, mode={}'.format(is_gui, mode))

        # The flask app
        self.app = Flask(__name__,
                         static_folder=self.common.get_resource_path('static'),
                         template_folder=self.common.get_resource_path('templates'))
        self.app.secret_key = self.common.random_string(8)
        self.auth = HTTPBasicAuth()
        self.auth.error_handler(self.error401)

        # Verbose mode?
        if self.common.verbose:
            self.verbose_mode()

        # Are we running in GUI mode?
        self.is_gui = is_gui

        # If the user stops the server while a transfer is in progress, it should
        # immediately stop the transfer. In order to make it thread-safe, stop_q
        # is a queue. If anything is in it, then the user stopped the server
        self.stop_q = queue.Queue()

        # Are we using receive mode?
        self.mode = mode
        if self.mode == 'receive':
            # Use custom WSGI middleware, to modify environ
            self.app.wsgi_app = ReceiveModeWSGIMiddleware(self.app.wsgi_app, self)
            # Use a custom Request class to track upload progess
            self.app.request_class = ReceiveModeRequest

        # Starting in Flask 0.11, render_template_string autoescapes template variables
        # by default. To prevent content injection through template variables in
        # earlier versions of Flask, we force autoescaping in the Jinja2 template
        # engine if we detect a Flask version with insecure default behavior.
        if Version(flask_version) < Version('0.11'):
            # Monkey-patch in the fix from https://github.com/pallets/flask/commit/99c99c4c16b1327288fd76c44bc8635a1de452bc
            Flask.select_jinja_autoescape = self._safe_select_jinja_autoescape

        self.security_headers = [
            ('Content-Security-Policy', 'default-src \'self\'; style-src \'self\'; script-src \'self\'; img-src \'self\' data:;'),
            ('X-Frame-Options', 'DENY'),
            ('X-Xss-Protection', '1; mode=block'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Referrer-Policy', 'no-referrer'),
            ('Server', 'OnionShare')
        ]

        self.q = queue.Queue()
        self.slug = None

        self.reset_invalid_slugs()

        self.done = False

        # shutting down the server only works within the context of flask, so the easiest way to do it is over http
        self.shutdown_slug = self.common.random_string(16)

        # Keep track if the server is running
        self.running = False

        # Define the web app routes
        self.define_common_routes()

        # Create the mode web object, which defines its own routes
        self.share_mode = None
        self.receive_mode = None
        if self.mode == 'receive':
            self.receive_mode = ReceiveModeWeb(self.common, self)
        elif self.mode == 'website':
            self.website_mode = WebsiteModeWeb(self.common, self)
        elif self.mode == 'share':
            self.share_mode = ShareModeWeb(self.common, self)


    def define_common_routes(self):
        """
        Common web app routes between all modes.
        """

        @self.auth.get_password
        def get_pw(username):
            if username == 'onionshare':
                return self.slug
            else:
                return None

        @self.app.before_request
        def conditional_auth_check():
            if not self.common.settings.get('public_mode'):
                @self.auth.login_required
                def _check_login():
                    return None

                return _check_login()

        @self.app.errorhandler(404)
        def not_found(e):
            return self.error404()

        @self.app.route("/<slug_candidate>/shutdown")
        def shutdown(slug_candidate):
            """
            Stop the flask web server, from the context of an http request.
            """
            if slug_candidate == self.shutdown_slug:
                self.force_shutdown()
                return ""
            abort(404)

        @self.app.route("/noscript-xss-instructions")
        def noscript_xss_instructions():
            """
            Display instructions for disabling Tor Browser's NoScript XSS setting
            """
            r = make_response(render_template('receive_noscript_xss.html'))
            return self.add_security_headers(r)

    def error401(self):
        auth = request.authorization
        if auth:
            if auth['username'] == 'onionshare' and auth['password'] not in self.invalid_slugs:
                print('Invalid password guess: {}'.format(auth['password']))
                self.add_request(Web.REQUEST_INVALID_SLUG, data=auth['password'])

                self.invalid_slugs.append(auth['password'])
                self.invalid_slugs_count += 1

                if self.invalid_slugs_count == 20:
                    self.add_request(Web.REQUEST_RATE_LIMIT)
                    self.force_shutdown()
                    print("Someone has made too many wrong attempts to guess your password, so OnionShare has stopped the server. Start sharing again and send the recipient a new address to share.")

        r = make_response(render_template('401.html'), 401)
        return self.add_security_headers(r)

    def error404(self):
        self.add_request(Web.REQUEST_OTHER, request.path)
        r = make_response(render_template('404.html'), 404)
        return self.add_security_headers(r)

    def error403(self):
        self.add_request(Web.REQUEST_OTHER, request.path)

        r = make_response(render_template('403.html'), 403)
        return self.add_security_headers(r)

    def add_security_headers(self, r):
        """
        Add security headers to a request
        """
        for header, value in self.security_headers:
            r.headers.set(header, value)
        return r

    def _safe_select_jinja_autoescape(self, filename):
        if filename is None:
            return True
        return filename.endswith(('.html', '.htm', '.xml', '.xhtml'))

    def add_request(self, request_type, path=None, data=None):
        """
        Add a request to the queue, to communicate with the GUI.
        """
        self.q.put({
            'type': request_type,
            'path': path,
            'data': data
        })

    def generate_slug(self, persistent_slug=None):
        self.common.log('Web', 'generate_slug', 'persistent_slug={}'.format(persistent_slug))
        if persistent_slug != None and persistent_slug != '':
            self.slug = persistent_slug
            self.common.log('Web', 'generate_slug', 'persistent_slug sent, so slug is: "{}"'.format(self.slug))
        else:
            self.slug = self.common.build_slug()
            self.common.log('Web', 'generate_slug', 'built random slug: "{}"'.format(self.slug))

    def verbose_mode(self):
        """
        Turn on verbose mode, which will log flask errors to a file.
        """
        flask_log_filename = os.path.join(self.common.build_data_dir(), 'flask.log')
        log_handler = logging.FileHandler(flask_log_filename)
        log_handler.setLevel(logging.WARNING)
        self.app.logger.addHandler(log_handler)

    def reset_invalid_slugs(self):
        self.invalid_slugs_count = 0
        self.invalid_slugs = []

    def force_shutdown(self):
        """
        Stop the flask web server, from the context of the flask app.
        """
        # Shutdown the flask service
        try:
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
        except:
            pass
        self.running = False

    def start(self, port, stay_open=False, public_mode=False, slug=None):
        """
        Start the flask web server.
        """
        self.common.log('Web', 'start', 'port={}, stay_open={}, public_mode={}, slug={}'.format(port, stay_open, public_mode, slug))

        self.stay_open = stay_open

        # Make sure the stop_q is empty when starting a new server
        while not self.stop_q.empty():
            try:
                self.stop_q.get(block=False)
            except queue.Empty:
                pass

        # In Whonix, listen on 0.0.0.0 instead of 127.0.0.1 (#220)
        if os.path.exists('/usr/share/anon-ws-base-files/workstation'):
            host = '0.0.0.0'
        else:
            host = '127.0.0.1'

        self.running = True
        self.app.run(host=host, port=port, threaded=True)

    def stop(self, port):
        """
        Stop the flask web server by loading /shutdown.
        """
        self.common.log('Web', 'stop', 'stopping server')

        # Let the mode know that the user stopped the server
        self.stop_q.put(True)

        # To stop flask, load http://shutdown:[shutdown_slug]@127.0.0.1/[shutdown_slug]/shutdown
        # (We're putting the shutdown_slug in the path as well to make routing simpler)
        if self.running:
            requests.get('http://127.0.0.1:{}/{}/shutdown'.format(port, self.shutdown_slug),
                auth=requests.auth.HTTPBasicAuth('onionshare', self.slug))

        # Reset any slug that was in use
        self.slug = None
