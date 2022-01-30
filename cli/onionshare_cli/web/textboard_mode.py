from flask import request, render_template, make_response, jsonify, session
from flask_socketio import emit, ConnectionRefusedError

class TextboardModeWeb:
    def __init__(self, common, web):
        self.common = common
        self.common.log("ChatModeWeb", "__init__")

        self.web = web

        # Whether or not we can send REQUEST_INDIVIDUAL_FILE_STARTED
        # and maybe other events when requests come in to this mode
        # Chat mode has no concept of individual file requests that
        # turn into history widgets in the GUI, so set it to False
        self.supports_file_requests = False # idk what to with this

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for textboard
        """
        
        @self.web.app.route("/", methods=["GET"], provide_automatic_options=False)
        def index():
            return render_template(
                "textboard.html",
                static_url_path=self.web.static_url_path,
                title=self.web.settings.get("general", "title")
            )