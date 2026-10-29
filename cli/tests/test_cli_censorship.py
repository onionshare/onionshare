import pytest

from onionshare_cli import censorship, common


class FakeMeek:
    """Stands in for a running meek-client, so api_proxies is populated."""

    meek_proxies = {
        "http": "socks5h://127.0.0.1:1",
        "https": "socks5h://127.0.0.1:1",
    }


class FakeResponse:
    status_code = 200

    def json(self):
        return {"settings": []}


@pytest.fixture
def circumvention_obj():
    return censorship.CensorshipCircumvention(common.Common(), FakeMeek())


@pytest.fixture
def captured_request(monkeypatch):
    """Capture the request body that would go to the Moat API."""
    captured = {}

    def fake_post(endpoint, json=None, headers=None, proxies=None):
        captured["endpoint"] = endpoint
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(censorship.requests, "post", fake_post)
    return captured


class TestRequestSettings:
    def test_country_is_sent(self, circumvention_obj, captured_request):
        circumvention_obj.request_settings(country="de")
        assert captured_request["json"] == {"country": "de"}

    def test_transports_are_sent(self, circumvention_obj, captured_request):
        circumvention_obj.request_settings(
            country="de", transports=["obfs4", "snowflake"]
        )
        assert captured_request["json"] == {
            "country": "de",
            "transports": ["obfs4", "snowflake"],
        }

    def test_transports_are_sent_without_a_country(
        self, circumvention_obj, captured_request
    ):
        circumvention_obj.request_settings(transports=["obfs4"])
        assert captured_request["json"] == {"transports": ["obfs4"]}


class FakeOnion:
    """Stands in for Onion, with a controllable Tor connection state."""

    def __init__(self, authenticated):
        self.authenticated = authenticated

    def is_authenticated(self):
        return self.authenticated

    def get_tor_socks_port(self):
        return ("127.0.0.1", 9050)


class TestOverTor:
    def test_uses_tor_socks_proxy_when_connected(self):
        c = censorship.CensorshipCircumvention(
            common.Common(), onion=FakeOnion(authenticated=True)
        )
        assert c.api_proxies == {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }

    def test_no_proxy_when_tor_not_connected(self):
        # Must not raise (returning a value from __init__ is a TypeError)
        c = censorship.CensorshipCircumvention(
            common.Common(), onion=FakeOnion(authenticated=False)
        )
        assert c.api_proxies == {}

    def test_no_request_sent_when_tor_not_connected(self, monkeypatch):
        def fail(*args, **kwargs):
            raise AssertionError("request sent without a proxy")

        monkeypatch.setattr(censorship.requests, "post", fail)
        monkeypatch.setattr(censorship.requests, "get", fail)
        c = censorship.CensorshipCircumvention(
            common.Common(), onion=FakeOnion(authenticated=False)
        )
        assert c.request_builtin_bridges() is False
