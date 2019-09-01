import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response

from .send_base_mode import SendBaseModeWeb
from .. import strings


class WebsiteModeWeb(SendBaseModeWeb):
    """
    All of the web logic for website mode
    """
    def init(self):
        self.common.log('WebsiteModeWeb', '__init__')
        self.define_routes()


    def define_routes(self):
        """
        The web app routes for sharing a website
        """

        @self.web.app.route('/', defaults={'path': ''})
        @self.web.app.route('/<path:path>')
        def path_public(path):
            return path_logic(path)

        def path_logic(path=''):
            """
            Render the onionshare website.
            """

            # Each download has a unique id
            visit_id = self.visit_count
            self.visit_count += 1

            # Tell GUI the page has been visited
            self.web.add_request(self.web.REQUEST_STARTED, path, {
                'id': visit_id,
                'action': 'visit'
            })

            return self.render_logic(path)
