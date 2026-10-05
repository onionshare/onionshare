import sys
import unittest

from PySide6 import QtWidgets

from onionshare import strings
from onionshare.widgets import Alert


class TestAlert(unittest.TestCase):
    """
    Alert's standard buttons (e.g. "OK") must be re-labeled from OnionShare's
    own locale strings, since Qt's built-in translations for QMessageBox
    standard buttons are never loaded (OnionShare has no QTranslator for
    Qt's own qtbase locale files). See onionshare/onionshare#984.
    """

    def setUp(self):
        self.common = sys.onionshare_common
        self.original_strings = strings.strings
        # Use a fake, distinguishable translation to prove the button text
        # comes from our strings dict and not from Qt's own defaults.
        strings.strings = dict(self.original_strings)
        strings.strings["gui_alert_button_ok"] = "TRANSLATED_OK"
        strings.strings["gui_alert_button_cancel"] = "TRANSLATED_CANCEL"

    def tearDown(self):
        strings.strings = self.original_strings

    def test_ok_button_is_translated(self):
        alert = Alert(self.common, "test message", autostart=False)
        ok_button = alert.button(QtWidgets.QMessageBox.Ok)
        self.assertIsNotNone(ok_button)
        self.assertEqual(ok_button.text(), "TRANSLATED_OK")

    def test_multiple_standard_buttons_are_translated(self):
        alert = Alert(
            self.common,
            "test message",
            buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
            autostart=False,
        )
        self.assertEqual(
            alert.button(QtWidgets.QMessageBox.Ok).text(), "TRANSLATED_OK"
        )
        self.assertEqual(
            alert.button(QtWidgets.QMessageBox.Cancel).text(), "TRANSLATED_CANCEL"
        )

    def test_custom_buttons_are_left_untouched(self):
        # Alerts built with buttons=NoButton and their own QPushButtons
        # (e.g. MainWindow.tor_connection_canceled) must not be affected.
        alert = Alert(
            self.common,
            "test message",
            buttons=QtWidgets.QMessageBox.NoButton,
            autostart=False,
        )
        custom_button = QtWidgets.QPushButton("Custom")
        alert.addButton(custom_button, QtWidgets.QMessageBox.AcceptRole)
        self.assertEqual(custom_button.text(), "Custom")


if __name__ == "__main__":
    unittest.main()
