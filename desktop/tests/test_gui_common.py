import json
import os

from onionshare.gui_common import GuiCommon
from onionshare import strings

LOCALE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "onionshare", "resources", "locale"
)


class TestGetTranslatedBootstrapSummary:
    """
    GuiCommon.get_translated_bootstrap_summary() translates a Tor
    bootstrap-phase summary (see control-spec.txt Section 5.5) using its
    stable "tag", so the "Connecting to Tor" progress messages (#982) show
    up in the user's locale instead of always in English.
    """

    @classmethod
    def setup_class(cls):
        with open(os.path.join(LOCALE_DIR, "en.json"), encoding="utf-8") as f:
            strings.strings = json.load(f)

    def test_known_tag_is_translated(self):
        assert (
            GuiCommon.get_translated_bootstrap_summary("done", "raw fallback")
            == strings.strings["gui_bootstrap_status_done"]
        )
        assert (
            GuiCommon.get_translated_bootstrap_summary(
                "loading_descriptors", "raw fallback"
            )
            == strings.strings["gui_bootstrap_status_loading_descriptors"]
        )

    def test_unknown_tag_falls_back_to_raw_summary(self):
        # A hypothetical tag from a future Tor version that OnionShare
        # doesn't know about yet must not crash, and must keep showing
        # Tor's own (English) summary text rather than an error.
        assert (
            GuiCommon.get_translated_bootstrap_summary(
                "some_future_tag", "Tor's own text"
            )
            == "Tor's own text"
        )
