import sys
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt


class TestApplicationIsDarkMode(unittest.TestCase):
    """
    Application.is_dark_mode() must reflect the platform's actual color
    scheme. It previously read the Base color of a bare, style-independent
    QPalette(), which does not reliably track the OS light/dark setting
    (e.g. it's reset by the Fusion style applied on Windows/macOS just
    before this check runs). See onionshare/onionshare#1440.
    """

    def setUp(self):
        self.qtapp = sys.onionshare_qtapp
        self.original_style_hints = self.qtapp.styleHints

    def tearDown(self):
        self.qtapp.styleHints = self.original_style_hints

    def _patch_color_scheme(self, color_scheme):
        style_hints = MagicMock()
        style_hints.colorScheme.return_value = color_scheme
        self.qtapp.styleHints = lambda: style_hints

    def test_dark_color_scheme_is_dark_mode(self):
        self._patch_color_scheme(Qt.ColorScheme.Dark)
        self.assertTrue(self.qtapp.is_dark_mode())

    def test_light_color_scheme_is_not_dark_mode(self):
        self._patch_color_scheme(Qt.ColorScheme.Light)
        self.assertFalse(self.qtapp.is_dark_mode())

    def test_unknown_color_scheme_falls_back_to_light(self):
        self._patch_color_scheme(Qt.ColorScheme.Unknown)
        self.assertFalse(self.qtapp.is_dark_mode())


if __name__ == "__main__":
    unittest.main()
