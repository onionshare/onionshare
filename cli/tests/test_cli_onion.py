from onionshare_cli import onion as onion_module
from onionshare_cli.onion import Onion


class FakeSettings:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        pass


class FakeCommon:
    def log(self, *args, **kwargs):
        pass


class FakeMeek:
    def __init__(self, common):
        pass

    def start(self):
        pass

    def cleanup(self):
        pass


def make_onion(monkeypatch, authenticated):
    # Skip Onion.__init__, which sets up a real Tor environment
    o = Onion.__new__(Onion)
    o.common = FakeCommon()
    o.settings = FakeSettings()
    monkeypatch.setattr(o, "is_authenticated", lambda: authenticated)
    return o


def record_circumvention(monkeypatch, bridges):
    """Replace CensorshipCircumvention and record how it is constructed."""
    calls = []

    class FakeCircumvention:
        def __init__(self, common, meek=None, onion=None):
            calls.append({"meek": meek, "onion": onion})

        def request_builtin_bridges(self):
            return bridges

    monkeypatch.setattr(onion_module, "CensorshipCircumvention", FakeCircumvention)
    monkeypatch.setattr(onion_module, "Meek", FakeMeek)
    return calls


class TestUpdateBuiltinBridges:
    def test_skips_tor_when_not_connected(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=False)
        calls = record_circumvention(monkeypatch, {"obfs4": ["bridge"]})
        o.update_builtin_bridges()
        # Only the Meek attempt is made
        assert len(calls) == 1
        assert calls[0]["onion"] is None
        assert isinstance(calls[0]["meek"], FakeMeek)

    def test_tries_tor_first_when_connected(self, monkeypatch):
        o = make_onion(monkeypatch, authenticated=True)
        calls = record_circumvention(monkeypatch, {"obfs4": ["bridge"]})
        o.update_builtin_bridges()
        assert len(calls) == 1
        assert calls[0]["onion"] is o
        assert calls[0]["meek"] is None
        assert o.settings.get("bridges_builtin") == {"obfs4": ["bridge"]}
