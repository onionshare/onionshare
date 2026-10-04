import sys
import unittest

from PySide6 import QtCore, QtWidgets

from onionshare.gui_common import GuiCommon
from onionshare.tab.mode.mode_settings_widget import ModeSettingsWidget
from onionshare.tab.server_status import ServerStatus

FIXED_DATETIME = QtCore.QDateTime(QtCore.QDate(2027, 3, 9), QtCore.QTime(14, 5, 0))


class FakeModeSettings:
    def __init__(self):
        self._settings = {
            "persistent": {
                "mode": None,
                "enabled": False,
                "autostart_on_launch": False,
            },
            "general": {
                "title": None,
                "public": False,
                "autostart_timer": True,
                "autostop_timer": True,
            },
        }

    def get(self, group, key):
        return self._settings[group][key]

    def set(self, group, key, value):
        self._settings[group][key] = value


class FakeTab:
    mode = None
    tab_id = 0


class TestTimerLocale(unittest.TestCase):
    """
    The auto-start/auto-stop timer widgets and the server button tooltips
    must show a 24-hour clock in locales where that is the norm, with
    localized month names, while keeping the traditional date ordering for
    OnionShare's generic English locale (which resolves to QLocale("en_US")
    and would otherwise show month-first dates like 3/9/27).
    """

    @classmethod
    def setUpClass(cls):
        cls.common = sys.onionshare_common
        cls.qtapp = sys.onionshare_qtapp
        if not hasattr(cls.common, "gui") or cls.common.gui is None:
            cls.common.gui = GuiCommon(cls.common, cls.qtapp, local_only=True)

    def setUp(self):
        self.original_locale = self.common.settings.get("locale")

    def tearDown(self):
        self.common.settings.set("locale", self.original_locale)

    def make_mode_settings_widget(self):
        return ModeSettingsWidget(self.common, FakeTab(), FakeModeSettings())

    def make_server_status(self, widget):
        return ServerStatus(
            self.common,
            self.qtapp,
            app=None,
            mode_settings=FakeModeSettings(),
            mode_settings_widget=widget,
            local_only=True,
        )

    def test_no_available_locale_falls_back_to_c(self):
        for code in self.common.settings.available_locales:
            locale = QtCore.QLocale(code)
            self.assertNotEqual(
                locale.name(),
                "C",
                f"QLocale({code!r}) is not a valid locale",
            )

    def test_english_widget_uses_24h_and_traditional_date(self):
        self.common.settings.set("locale", "en")
        widget = self.make_mode_settings_widget()
        widget.autostart_timer_widget.setDateTime(FIXED_DATETIME)
        self.assertEqual(
            widget.autostart_timer_widget.text(),
            "14:05 Mar 9, 27",
        )

    def test_english_tooltip_uses_24h_and_traditional_date(self):
        self.common.settings.set("locale", "en")
        widget = self.make_mode_settings_widget()
        widget.autostop_timer_widget.setDateTime(FIXED_DATETIME)
        server_status = self.make_server_status(widget)
        self.assertEqual(
            server_status.timer_datetime_string(widget.autostop_timer_widget),
            "14:05, March 09, 2027",
        )

    def test_french_widget_uses_24h_and_french_date(self):
        self.common.settings.set("locale", "fr")
        widget = self.make_mode_settings_widget()
        widget.autostart_timer_widget.setDateTime(FIXED_DATETIME)
        self.assertEqual(
            widget.autostart_timer_widget.text(),
            "14:05 09/03/2027",
        )

    def test_french_tooltip_uses_24h_and_french_date(self):
        self.common.settings.set("locale", "fr")
        widget = self.make_mode_settings_widget()
        widget.autostop_timer_widget.setDateTime(FIXED_DATETIME)
        server_status = self.make_server_status(widget)
        self.assertEqual(
            server_status.timer_datetime_string(widget.autostop_timer_widget),
            "14:05, mardi 9 mars 2027",
        )

    def test_german_widget_uses_24h_and_german_date(self):
        self.common.settings.set("locale", "de")
        widget = self.make_mode_settings_widget()
        widget.autostart_timer_widget.setDateTime(FIXED_DATETIME)
        self.assertEqual(
            widget.autostart_timer_widget.text(),
            "14:05 09.03.27",
        )

    def test_german_tooltip_uses_24h_and_german_date(self):
        self.common.settings.set("locale", "de")
        widget = self.make_mode_settings_widget()
        widget.autostop_timer_widget.setDateTime(FIXED_DATETIME)
        server_status = self.make_server_status(widget)
        self.assertEqual(
            server_status.timer_datetime_string(widget.autostop_timer_widget),
            "14:05, Dienstag, 9. März 2027",
        )

    def test_japanese_tooltip_uses_24h_and_japanese_date(self):
        self.common.settings.set("locale", "ja")
        widget = self.make_mode_settings_widget()
        widget.autostop_timer_widget.setDateTime(FIXED_DATETIME)
        server_status = self.make_server_status(widget)
        self.assertEqual(
            server_status.timer_datetime_string(widget.autostop_timer_widget),
            "14:05, 2027年3月9日火曜日",
        )

    def test_traditional_chinese_widget_keeps_its_own_am_pm(self):
        # zh_Hant is one of the locales whose CLDR short time format is 12-hour
        self.common.settings.set("locale", "zh_Hant")
        widget = self.make_mode_settings_widget()
        widget.autostart_timer_widget.setDateTime(FIXED_DATETIME)
        self.assertNotIn("14:05", widget.autostart_timer_widget.text())
        self.assertEqual(
            widget.autostart_timer_widget.text(),
            "下午2:05 2027/3/9",
        )

    def test_set_datetime_round_trips_through_the_widget(self):
        # The GUI tests set a timer via setDateTime() and compare against
        # dateTime(), so the new display format must not corrupt the value
        for code in ["en", "fr", "de", "nb_NO", "ja", "zh_Hans", "ru", "ar", "pt_BR", "zh_Hant"]:
            self.common.settings.set("locale", code)
            widget = self.make_mode_settings_widget()
            widget.autostart_timer_widget.setDateTime(FIXED_DATETIME)
            self.assertEqual(
                widget.autostart_timer_widget.dateTime(),
                FIXED_DATETIME,
                f"Round-trip failed for locale {code!r}",
            )
            widget.autostart_timer_widget.setCurrentSection(
                QtWidgets.QDateTimeEdit.MinuteSection
            )
            self.assertEqual(
                widget.autostart_timer_widget.dateTime(),
                FIXED_DATETIME,
                f"setCurrentSection corrupted the value for locale {code!r}",
            )


if __name__ == "__main__":
    unittest.main()
