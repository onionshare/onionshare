import hmac
import logging
import os
import queue
import socket
import sys
import tempfile
from distutils.version import LooseVersion as Version
from urllib.request import urlopen

import flask
from flask import Flask, request, render_template, abort, make_response, __version__ as flask_version

from .. import strings

from .share_mode import ShareModeWeb
from .receive_mode import ReceiveModeWeb, ReceiveModeWSGIMiddleware, ReceiveModeRequest


# Stub out flask's show_server_banner function, to avoiding showing warnings that
# are not applicable to OnionShare
def stubbed_show_server_banner(env, debug, app_import_path, eager_loading):
    pass

flask.cli.show_server_banner = stubbed_show_server_banner


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

    def __init__(self, common, is_gui, mode='share'):
        self.common = common
        self.common.log('Web', '__init__', 'is_gui={}, mode={}'.format(is_gui, mode))

        # The flask app
        self.app = Flask(__name__,
                         static_folder=self.common.get_resource_path('static'),
                         template_folder=self.common.get_resource_path('templates'))
        self.app.secret_key = self.common.random_string(8)

        # Debug mode?
        if self.common.debug:
            self.debug_mode()

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
        self.error404_count = 0

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
        elif self.mode == 'share':
            self.share_mode = ShareModeWeb(self.common, self)


    def define_common_routes(self):
        """
        Common web app routes between sending and receiving
        """
        @self.app.errorhandler(404)
        def page_not_found(e):
            """
            404 error page.
            """
            return self.error404()

        @self.app.route("/<slug_candidate>/shutdown")
        def shutdown(slug_candidate):
            """
            Stop the flask web server, from the context of an http request.
            """
            self.check_shutdown_slug_candidate(slug_candidate)
            self.force_shutdown()
            return ""

        @self.app.route("/noscript-xss-instructions")
        def noscript_xss_instructions():
            """
            Display instructions for disabling Tor Browser's NoScript XSS setting
            """
            r = make_response(render_template('receive_noscript_xss.html'))
            return self.add_security_headers(r)

    def error404(self):
        self.add_request(Web.REQUEST_OTHER, request.path)
        if request.path != '/favicon.ico':
            self.error404_count += 1

            # In receive mode, with public mode enabled, skip rate limiting 404s
            if not self.common.settings.get('public_mode'):
                if self.error404_count == 20:
                    self.add_request(Web.REQUEST_RATE_LIMIT, request.path)
                    self.force_shutdown()
                    print(strings._('error_rate_limit'))

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

    def add_request(self, request_type, path, data=None):
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

    def debug_mode(self):
        """
        Turn on debugging mode, which will log flask errors to a debug file.
        """
        flask_debug_filename = os.path.join(self.common.build_data_dir(), 'flask_debug.log')
        log_handler = logging.FileHandler(flask_debug_filename)
        log_handler.setLevel(logging.WARNING)
        self.app.logger.addHandler(log_handler)

    def check_slug_candidate(self, slug_candidate):
        self.common.log('Web', 'check_slug_candidate: slug_candidate={}'.format(slug_candidate))
        if self.common.settings.get('public_mode'):
            abort(404)
        if not hmac.compare_digest(self.slug, slug_candidate):
            abort(404)

    def check_shutdown_slug_candidate(self, slug_candidate):
        self.common.log('Web', 'check_shutdown_slug_candidate: slug_candidate={}'.format(slug_candidate))
        if not hmac.compare_digest(self.shutdown_slug, slug_candidate):
            abort(404)

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

    def start(self, port, stay_open=False, public_mode=False, persistent_slug=None):
        """
        Start the flask web server.
        """
        self.common.log('Web', 'start', 'port={}, stay_open={}, public_mode={}, persistent_slug={}'.format(port, stay_open, public_mode, persistent_slug))
        if not public_mode:
            self.generate_slug(persistent_slug)

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

        # Reset any slug that was in use
        self.slug = ''

        # To stop flask, load http://127.0.0.1:<port>/<shutdown_slug>/shutdown
        if self.running:
            try:
                s = socket.socket()
                s.connect(('127.0.0.1', port))
                s.sendall('GET /{0:s}/shutdown HTTP/1.1\r\n\r\n'.format(self.shutdown_slug))
            except:
                try:
                    urlopen('http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(port, self.shutdown_slug)).read()
                except:
                    pass
