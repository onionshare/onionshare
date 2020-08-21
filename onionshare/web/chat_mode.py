from flask import (
    Request,
    request,
    render_template,
    make_response,
    jsonify,
    redirect,
    session,
)
from werkzeug.utils import secure_filename
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

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for chatting
        """

        @self.web.app.route("/")
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
                request.path, {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            r = make_response(
                render_template(
                    "chat.html",
                    static_url_path=self.web.static_url_path,
                    username=session.get("name"),
                )
            )
            return self.web.add_security_headers(r)

        @self.web.app.route("/update-session-username", methods=["POST"])
        def update_session_username():
            history_id = self.cur_history_id
            data = request.get_json()
            if data.get("username", "") not in self.connected_users:
                session["name"] = data.get("username", session.get("name"))
            self.web.add_request(
                request.path, {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            r = make_response(jsonify(username=session.get("name"), success=True,))
            return self.web.add_security_headers(r)

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
            if message["username"] not in self.connected_users:
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
