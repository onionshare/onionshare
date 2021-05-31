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

from flask import request, render_template, make_response, jsonify, session
from flask_socketio import emit, join_room, leave_room


class ChatModeWeb:
    """
    All of the web logic for chat mode
    """

    def __init__(self, common, web):
        self.common = common
        self.common.log("ChatModeWeb", "__init__")

        self.web = web

        # This tracks users in the room
        self.connected_users = []

        # This tracks the history id
        self.cur_history_id = 0

        # Whether or not we can send REQUEST_INDIVIDUAL_FILE_STARTED
        # and maybe other events when requests come in to this mode
        # Chat mode has no concept of individual file requests that
        # turn into history widgets in the GUI, so set it to False
        self.supports_file_requests = False

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for chatting
        """

        @self.web.app.route("/", methods=["GET"], provide_automatic_options=False)
        def index():
            history_id = self.cur_history_id
            self.cur_history_id += 1
            session["name"] = (
                session.get("name")
                if session.get("name")
                else self.common.build_username()
            )
            session["room"] = self.web.settings.default_settings["chat"]["room"]
            self.web.add_request(
                request.path,
                {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            return render_template(
                    "chat.html",
                    static_url_path=self.web.static_url_path,
                    username=session.get("name"),
                    title=self.web.settings.get("general", "title"),
                )
            )

        @self.web.app.route("/update-session-username", methods=["POST"], provide_automatic_options=False)
        def update_session_username():
            history_id = self.cur_history_id
            data = request.get_json()
            if (
                data.get("username", "")
                and data.get("username", "") not in self.connected_users
                and len(data.get("username", "")) < 128
            ):
                session["name"] = data.get("username", session.get("name"))
                self.web.add_request(
                    request.path,
                    {"id": history_id, "status_code": 200},
                )

                self.web.add_request(self.web.REQUEST_LOAD, request.path)
                r = make_response(
                    jsonify(
                        username=session.get("name"),
                        success=True,
                    )
                )
            else:
                self.web.add_request(
                    request.path,
                    {"id": history_id, "status_code": 403},
                )

                r = make_response(
                    jsonify(
                        username=session.get("name"),
                        success=False,
                    )
                )
            return r

        @self.web.socketio.on("joined", namespace="/chat")
        def joined(message):
            """Sent by clients when they enter a room.
            A status message is broadcast to all people in the room."""
            self.connected_users.append(session.get("name"))
            join_room(session.get("room"))
            emit(
                "status",
                {
                    "username": session.get("name"),
                    "msg": "{} has joined.".format(session.get("name")),
                    "connected_users": self.connected_users,
                    "user": session.get("name"),
                },
                room=session.get("room"),
            )

        @self.web.socketio.on("text", namespace="/chat")
        def text(message):
            """Sent by a client when the user entered a new message.
            The message is sent to all people in the room."""
            emit(
                "message",
                {"username": session.get("name"), "msg": message["msg"]},
                room=session.get("room"),
            )

        @self.web.socketio.on("update_username", namespace="/chat")
        def update_username(message):
            """Sent by a client when the user updates their username.
            The message is sent to all people in the room."""
            current_name = session.get("name")
            if message.get("username", ""):
                session["name"] = message["username"]
                self.connected_users[
                    self.connected_users.index(current_name)
                ] = session.get("name")
            emit(
                "status",
                {
                    "msg": "{} has updated their username to: {}".format(
                        current_name, session.get("name")
                    ),
                    "connected_users": self.connected_users,
                    "old_name": current_name,
                    "new_name": session.get("name"),
                },
                room=session.get("room"),
            )

        @self.web.socketio.on("disconnect", namespace="/chat")
        def disconnect():
            """Sent by clients when they disconnect from a room.
            A status message is broadcast to all people in the room."""
            self.connected_users.remove(session.get("name"))
            leave_room(session.get("room"))
            emit(
                "status",
                {
                    "msg": "{} has left the room.".format(session.get("name")),
                    "connected_users": self.connected_users,
                },
                room=session.get("room"),
            )
