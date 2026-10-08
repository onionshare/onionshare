# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import os
import locale

# ONIONSHARE_<KEY> environment variables override settings. Unknown variables
# are ignored.
ENV_VAR_PREFIX = "ONIONSHARE_"

# "version" must always reflect the running OnionShare version.
NON_ENV_SETTINGS = {"version"}

# Types for settings whose default value is None.
ENV_SETTING_TYPES = {"locale": str, "autoupdate_timestamp": int}

# Tor's conventional environment variables, mapped to the settings they
# override. These have lower precedence than ONIONSHARE_* variables.
TOR_ENV_VARS = {
    "TOR_CONTROL_HOST": "control_port_address",
    "TOR_CONTROL_PORT": "control_port_port",
    "TOR_CONTROL_PASSWD": "auth_password",
    "TOR_CONTROL_COOKIE_AUTH_FILE": "cookie_auth_file",
}


class Settings(object):
    """
    This class stores all of the settings for OnionShare, specifically for how
    to connect to Tor. If it can't find the settings file, it uses the default,
    which is to attempt to connect automatically using default Tor Browser
    settings.
    """

    def __init__(self, common, config=False):
        self.common = common

        self.common.log("Settings", "__init__")

        # If a readable config file was provided, use that instead
        if config:
            if os.path.isfile(config):
                self.filename = config
            else:
                self.common.log(
                    "Settings",
                    "__init__",
                    "Supplied config does not exist or is unreadable. Falling back to default location",
                )
                self.filename = self.build_filename()

        else:
            # Default config
            self.filename = self.build_filename()

        # Dictionary of available languages in this version of OnionShare,
        # mapped to the language name, in that language
        self.available_locales = {
            "af": "Afrikaans",  # Afrikaans
            "sq": "Shqip",  # Albanian
            "ar": "العربية",  # Arabic
            "be": "Беларуская",  # Belarusian
            "bn": "বাংলা",  # Bengali
            "bg": "Български",  #Bulgarian
            "ca": "Català",  # Catalan
            "zh_Hant": "正體中文 (繁體)",  # Traditional Chinese
            "zh_Hans": "中文 (简体)",  # Simplified Chinese
            "hr": "Hrvatski",  # Croatian
            "cs": "čeština",  # Czech
            "da": "Dansk",  # Danish
            # "nl": "Nederlands",  # Dutch
            "en": "English",  # English
            "fi": "Suomi",  # Finnish
            "fr": "Français",  # French
            "gl": "Galego",  # Galician
            "de": "Deutsch",  # German
            "el": "Ελληνικά",  # Greek
            "is": "Íslenska",  # Icelandic
            "id": "Bahasa Indonesia",  # Indonesian
            "ga": "Gaeilge",  # Irish
            "it": "Italiano",  # Italian
            "ja": "日本語",  # Japanese
            "km": "ខ្មែរ",  # Khmer(Central)
            # "ckb": "Soranî",  # Kurdish (Central)
            "lt": "Lietuvių Kalba",  # Lithuanian
            "nb_NO": "Norsk Bokmål",  # Norwegian Bokmål
            "fa": "فارسی",  # Persian
            "pl": "Polski",  # Polish
            "pt_BR": "Português (Brasil)",  # Portuguese Brazil
            "pt_PT": "Português (Portugal)",  # Portuguese Portugal
            # "ro": "Română",  # Romanian
            "ru": "Русский",  # Russian
            "sn": "chiShona",  # Shona
            # "sr_Latn": "Srpska (latinica)",  # Serbian (latin)
            "sk": "Slovenčina",  # Slovak
            "es": "Español",  # Spanish
            "sw": "Kiswahili",  # Swahili
            "sv": "Svenska",  # Swedish
            "ta": "Tamil",    # Tamil
            # "te": "తెలుగు",  # Telugu
            "tr": "Türkçe",  # Turkish
            "uk": "Українська",  # Ukrainian
            "vi": "Tiếng Việt",  # Vietnamese
        }

        # These are the default settings. They will get overwritten when loading from disk
        self.default_settings = {
            "version": self.common.version,
            "connection_type": "bundled",
            "control_port_address": "127.0.0.1",
            "control_port_port": 9051,
            "socks_address": "127.0.0.1",
            "socks_port": 9050,
            "socket_file_path": "/var/run/tor/control",
            "cookie_auth_file": "/run/tor/control.authcookie",
            "auth_type": "no_auth",
            "auth_password": "",
            "auto_connect": False,
            "use_autoupdate": True,
            "autoupdate_timestamp": None,
            "bridges_enabled": False,
            "bridges_type": "built-in",  # "built-in", "moat", or "custom"
            "bridges_builtin_pt": "obfs4",  # "obfs4", "meek", or "snowflake"
            "bridges_moat": "",
            "bridges_custom": "",
            "bridges_builtin": {},
            "persistent_tabs": [],
            "locale": None,  # this gets defined in fill_in_defaults()
            "theme": 0,
        }
        self._settings = {}
        # Environment overrides, kept out of _settings so save() never writes them
        self._env_overrides = {}
        self.fill_in_defaults()

    def fill_in_defaults(self):
        """
        If there are any missing settings from self._settings, replace them with
        their default values.
        """
        for key in self.default_settings:
            if key not in self._settings:
                self._settings[key] = self.default_settings[key]

        # Choose the default locale based on the OS preference, and fall-back to English
        if self._settings["locale"] is None:
            language_code, encoding = locale.getlocale()

            # Default to English
            if not language_code:
                language_code = "en_US"

            if language_code == "pt_PT" and language_code == "pt_BR":
                # Portuguese locales include country code
                default_locale = language_code
            else:
                # All other locales cut off the country code
                default_locale = language_code[:2]

            if default_locale not in self.available_locales:
                default_locale = "en"
            self._settings["locale"] = default_locale

    def build_filename(self):
        """
        Returns the path of the settings file.
        """
        return os.path.join(self.common.build_data_dir(), "onionshare.json")

    def load(self):
        """
        Load the settings from file.
        """
        self.common.log("Settings", "load")

        # If the settings file exists, load it
        if os.path.exists(self.filename):
            try:
                self.common.log("Settings", "load", f"Trying to load {self.filename}")
                with open(self.filename, "r") as f:
                    self._settings = json.load(f)
                    self.fill_in_defaults()
            except Exception:
                pass

        # Apply environment overrides
        self._apply_env_overrides()

        # Make sure data_dir exists
        try:
            os.makedirs(self.get("data_dir"), exist_ok=True)
        except Exception:
            pass

    def _apply_env_overrides(self):
        """
        Apply TOR_* and ONIONSHARE_* environment overrides, in that order of
        precedence. They are kept out of self._settings so save() never persists
        them (e.g. an env-supplied auth_password).
        """
        self._env_overrides = {}
        self._apply_tor_env_vars()

        for key in self.default_settings:
            if key in NON_ENV_SETTINGS:
                continue

            env_key = f"{ENV_VAR_PREFIX}{key.upper()}"
            if env_key not in os.environ:
                continue

            try:
                value = self._parse_env_value(key, os.environ[env_key])
            except ValueError:
                # Keep the file/default value; don't log the bad value (may be a secret)
                self.common.log(
                    "Settings",
                    "_apply_env_overrides",
                    f"Ignoring invalid value for {env_key}",
                )
                continue

            self._env_overrides[key] = value

        if self._env_overrides:
            # Log names only, never values (may be secrets)
            self.common.log(
                "Settings",
                "_apply_env_overrides",
                "Overriding settings from environment: "
                + ", ".join(sorted(self._env_overrides)),
            )

    def _apply_tor_env_vars(self):
        """
        Apply Tor's conventional TOR_CONTROL_* environment variables. These
        have lower precedence than ONIONSHARE_* variables.
        """
        for env_key, key in TOR_ENV_VARS.items():
            raw = os.environ.get(env_key)
            if not raw:
                continue
            try:
                self._env_overrides[key] = self._parse_env_value(key, raw)
            except ValueError:
                self.common.log(
                    "Settings",
                    "_apply_tor_env_vars",
                    f"Ignoring invalid value for {env_key}",
                )

        # A password implies password authentication
        if "auth_password" in self._env_overrides:
            self._env_overrides["auth_type"] = "password"

        # These variables only apply to an explicit control port connection, so
        # select it, overriding the config file. ONIONSHARE_CONNECTION_TYPE is
        # applied afterwards, so it still wins. TOR_CONTROL_PORT is deliberately
        # excluded: it is also used to discover Tor in the "automatic"
        # connection type.
        tor_control_set = any(
            os.environ.get(env_key)
            for env_key in (
                "TOR_CONTROL_HOST",
                "TOR_CONTROL_PASSWD",
                "TOR_CONTROL_COOKIE_AUTH_FILE",
            )
        )
        if tor_control_set:
            self._env_overrides["connection_type"] = "control_port"

    def _parse_env_value(self, key, raw):
        """
        Parse an environment value by the setting's type. Raises ValueError.
        """
        expected_type = ENV_SETTING_TYPES.get(key, type(self.default_settings[key]))

        if expected_type is bool:
            return self._parse_env_bool(raw)

        if expected_type is int:
            return int(raw)

        if expected_type in (dict, list):
            value = json.loads(raw)
            if not isinstance(value, expected_type):
                raise ValueError(f"{key} must be a JSON {expected_type.__name__}")
            return value

        return raw

    @staticmethod
    def _parse_env_bool(raw):
        """
        Parse a boolean environment value. Raises ValueError.
        """
        value = raw.strip().lower()
        if value in ("1", "true", "yes", "on"):
            return True
        if value in ("0", "false", "no", "off"):
            return False
        raise ValueError("invalid boolean")

    def save(self):
        """
        Save settings to file.
        """
        self.common.log("Settings", "save")
        open(self.filename, "w").write(json.dumps(self._settings, indent=2))
        self.common.log("Settings", "save", f"Settings saved in {self.filename}")

    def get(self, key):
        # Environment overrides take precedence
        if key in self._env_overrides:
            return self._env_overrides[key]
        return self._settings[key]

    def set(self, key, val):
        # If typecasting int values fails, fallback to default values
        if key == "control_port_port" or key == "socks_port":
            try:
                val = int(val)
            except Exception:
                if key == "control_port_port":
                    val = self.default_settings["control_port_port"]
                elif key == "socks_port":
                    val = self.default_settings["socks_port"]

        # Keep an unchanged env override out of _settings so save() doesn't
        # persist it (the desktop sets every field on save). A different value
        # is an explicit choice and wins.
        if key in self._env_overrides:
            if val == self._env_overrides[key]:
                return
            self._env_overrides.pop(key, None)

        self._settings[key] = val
