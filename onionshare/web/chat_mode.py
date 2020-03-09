import os
import tempfile
import json
from datetime import datetime
from flask import Request, request, render_template, make_response, flash, redirect, session
from werkzeug.utils import secure_filename
from flask_socketio import emit, join_room, leave_room

from .. import strings


class ChatModeWeb:
    """
    All of the web logic for chat mode
    """

    def __init__(self, common, web):
        self.common = common
        self.common.log("ChatModeWeb", "__init__")

        self.web = web

        self.can_upload = True
        self.uploads_in_progress = []

        # This tracks the history id
        self.cur_history_id = 0

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for chatting
        """

        @self.web.app.route("/")
        def index():
            history_id = self.cur_history_id
            self.cur_history_id += 1
            self.web.add_request(
                request.path,
                {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            r = make_response(
                render_template(
                    "chat.html", static_url_path=self.web.static_url_path
                )
            )
            return self.web.add_security_headers(r)

        @self.web.socketio.on("joined", namespace="/chat")
        def joined(message):
            """Sent by clients when they enter a room.
            A status message is broadcast to all people in the room."""
            session["name"] = self.common.build_username()
            session["room"] = self.web.settings.default_settings["chat"]["room"]
            join_room(session.get("room"))
            emit(
                "status",
                {"msg": session.get("name") + " has entered the room."},
                room=session.get("room")
            )

        @self.web.socketio.on("text", namespace="/chat")
        def text(message):
            """Sent by a client when the user entered a new message.
            The message is sent to all people in the room."""
            emit(
                "message",
                {"msg": session.get("name") + ": " + message["msg"]},
                room=session.get("room")
            )
