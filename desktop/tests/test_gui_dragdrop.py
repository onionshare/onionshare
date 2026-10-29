from types import SimpleNamespace

from onionshare.tab.mode import file_selection


class FakeDragEvent:
    def __init__(self):
        self.ignored = False

    def ignore(self):
        self.ignored = True


def test_flatpak_drag_warning_is_deferred_until_handler_returns(monkeypatch):
    event = FakeDragEvent()
    common = SimpleNamespace(is_flatpak=lambda: True)
    file_list = SimpleNamespace(common=common)
    scheduled = []
    alerts = []

    monkeypatch.setattr(file_selection.strings, "_", lambda key: key)
    monkeypatch.setattr(
        file_selection.QtCore.QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )
    monkeypatch.setattr(
        file_selection,
        "Alert",
        lambda common, message: alerts.append(message),
    )

    file_selection.FileList.dragEnterEvent(file_list, event)

    assert event.ignored
    assert alerts == []
    assert len(scheduled) == 1

    delay, callback = scheduled[0]
    assert delay == 0
    callback()

    assert alerts == ["gui_dragdrop_sandbox_flatpak"]
