import pytest

from onionshare_cli.mode_settings import ModeSettings
from onionshare_cli.settings import Settings
from onionshare_cli.web import Web


@pytest.fixture
def chat_web(common_obj):
    common_obj.settings = Settings(common_obj)
    web = Web(common_obj, False, ModeSettings(common_obj), "chat")
    web.app.testing = True
    return web


def join(web, username=None):
    """
    A participant opens the chat, optionally picks a username over HTTP, and
    connects to the chat room. Returns their HTTP and Socket.IO test clients.
    """
    http = web.app.test_client()
    http.get("/")
    if username is not None:
        res = http.post("/update-session-username", json={"username": username})
        assert res.get_json() == {"username": username, "success": True}
    sio = web.socketio.test_client(web.app, namespace="/chat", flask_test_client=http)
    assert sio.is_connected("/chat")
    return http, sio


def set_name_over_http(http, username):
    return http.post("/update-session-username", json={"username": username}).get_json()


def set_name_over_socketio(sio, username):
    sio.get_received("/chat")
    sio.emit("update_username", {"username": username}, namespace="/chat")
    return [m["args"][0] for m in sio.get_received("/chat")]


IMPERSONATIONS = [
    # (name already in the chat, name someone else tries to take)
    ("alice", "аlice"),  # Cyrillic "а"
    ("alice", "‮ecila"),  # right-to-left override, displays as "alice"
    ("alice", "alice​"),  # zero-width space
    ("alice", "al­ice"),  # soft hyphen
    ("alice bob", "alice  bob"),  # runs of spaces display as one
    ("alice bob", "alice bob"),  # no-break space
    ("alice", "alice"),
]


class TestChatUsernames:
    @pytest.mark.parametrize("taken,impostor", IMPERSONATIONS)
    def test_impersonation_over_http(self, chat_web, taken, impostor):
        join(chat_web, taken)
        http, _ = join(chat_web)
        own_name = chat_web.chat_mode.connected_users[1]

        assert set_name_over_http(http, impostor) == {
            "username": own_name,
            "success": False,
        }

    @pytest.mark.parametrize("taken,impostor", IMPERSONATIONS)
    def test_impersonation_over_socketio(self, chat_web, taken, impostor):
        join(chat_web, taken)
        _, sio = join(chat_web)
        users_before = list(chat_web.chat_mode.connected_users)

        messages = set_name_over_socketio(sio, impostor)
        assert messages == [{"msg": "Failed to update username."}]
        assert chat_web.chat_mode.connected_users == users_before

    @pytest.mark.parametrize(
        "username",
        [
            "José",  # stored and shown as-is, but checked as "Jos"
            "bob!",
            "<b>bob</b>",
            "bob\nsmith",
            "bob​ smith",
            "a" + "​" * 5000,  # checked as "a", but 5001 characters long
            "a" * 128,
            "",
        ],
    )
    def test_invalid_usernames_rejected(self, chat_web, username):
        http, sio = join(chat_web)
        own_name = chat_web.chat_mode.connected_users[0]

        assert set_name_over_http(http, username) == {
            "username": own_name,
            "success": False,
        }
        assert set_name_over_socketio(sio, username) == [
            {"msg": "Failed to update username."}
        ]
        assert chat_web.chat_mode.connected_users == [own_name]

    @pytest.mark.parametrize(
        "username", ["bob", "Bob Smith", "bob-smith_2", "a" * 127, "x"]
    )
    def test_valid_usernames_accepted(self, chat_web, username):
        join(chat_web, "alice")
        http, sio = join(chat_web)
        old_name = chat_web.chat_mode.connected_users[1]

        assert set_name_over_http(http, f"  {username} ") == {
            "username": username,
            "success": True,
        }
        messages = set_name_over_socketio(sio, f" {username}  ")
        assert messages[0]["old_name"] == old_name
        assert messages[0]["new_name"] == username
        assert chat_web.chat_mode.connected_users == ["alice", username]

    def test_messages_carry_the_validated_name(self, chat_web):
        _, alice = join(chat_web, "alice")
        _, impostor = join(chat_web)
        set_name_over_socketio(impostor, "аlice")
        alice.get_received("/chat")

        impostor.emit("text", {"msg": "hi"}, namespace="/chat")
        received = [m["args"][0] for m in alice.get_received("/chat")]
        assert received == [
            {"username": chat_web.chat_mode.connected_users[1], "msg": "hi"}
        ]
        assert received[0]["username"] != "аlice"

    def test_generated_usernames_are_valid(self, chat_web):
        for _ in range(20):
            _, sio = join(chat_web)
        assert len(chat_web.chat_mode.connected_users) == 20
