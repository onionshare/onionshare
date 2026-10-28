# -*- coding: utf-8 -*-
"""Unit tests for error reporting in onionshare.threads (#2127)."""

from unittest import mock

import stem

from onionshare import strings
from onionshare.threads import OnionThread


def test_onion_thread_reports_exception_without_args(monkeypatch):
    monkeypatch.setattr(strings, "strings", {"error_generic": "Error:\n{}"})

    # stem raises SocketClosed() without a message when the Tor control socket closes
    mode = mock.MagicMock()
    mode.obtain_onion_early = False
    mode.app.start_onion_service.side_effect = stem.SocketClosed()

    errors = []
    thread = OnionThread(mode)
    thread.error.connect(errors.append)
    thread.run()

    assert errors == ["Error:\nSocketClosed"]


def test_onion_thread_reports_exception_message(monkeypatch):
    monkeypatch.setattr(strings, "strings", {"error_generic": "Error:\n{}"})

    mode = mock.MagicMock()
    mode.obtain_onion_early = False
    mode.app.start_onion_service.side_effect = RuntimeError("something broke")

    errors = []
    thread = OnionThread(mode)
    thread.error.connect(errors.append)
    thread.run()

    assert errors == ["Error:\nsomething broke"]
