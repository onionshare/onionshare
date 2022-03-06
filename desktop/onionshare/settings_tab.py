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

from PySide2 import QtCore, QtWidgets, QtGui
import platform
import datetime
from onionshare_cli.settings import Settings

from . import strings
from .widgets import Alert
from .update_checker import UpdateThread


class SettingsTab(QtWidgets.QWidget):
    """
    Settings dialog.
    """

    def __init__(self, common, tab_id, parent=None):
        super(SettingsTab, self).__init__()

        self.common = common
        self.common.log("SettingsTab", "__init__")

        self.system = platform.system()
        self.tab_id = tab_id
        self.parent = parent

        # Automatic updates options

        # Autoupdate
        self.autoupdate_checkbox = QtWidgets.QCheckBox()
        self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.autoupdate_checkbox.setText(strings._("gui_settings_autoupdate_option"))

        # Last update time
        self.autoupdate_timestamp = QtWidgets.QLabel()

        # Check for updates button
        self.check_for_updates_button = QtWidgets.QPushButton(
            strings._("gui_settings_autoupdate_check_button")
        )
        self.check_for_updates_button.clicked.connect(self.check_for_updates)
        # We can't check for updates if not connected to Tor
        if not self.common.gui.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)

        # Autoupdate options layout
        autoupdate_group_layout = QtWidgets.QVBoxLayout()
        autoupdate_group_layout.addWidget(self.autoupdate_checkbox)
        autoupdate_group_layout.addWidget(self.autoupdate_timestamp)
        autoupdate_group_layout.addWidget(self.check_for_updates_button)
        autoupdate_group = QtWidgets.QGroupBox(
            strings._("gui_settings_autoupdate_label")
        )
        autoupdate_group.setLayout(autoupdate_group_layout)

        autoupdate_layout = QtWidgets.QHBoxLayout()
        autoupdate_layout.addStretch()
        autoupdate_layout.addWidget(autoupdate_group)
        autoupdate_layout.addStretch()
        autoupdate_widget = QtWidgets.QWidget()
        autoupdate_widget.setLayout(autoupdate_layout)

        # Autoupdate is only available for Windows and Mac (Linux updates using package manager)
        if self.system != "Windows" and self.system != "Darwin":
            autoupdate_widget.hide()

        # Language settings
        language_label = QtWidgets.QLabel(strings._("gui_settings_language_label"))
        self.language_combobox = QtWidgets.QComboBox()
        # Populate the dropdown with all of OnionShare's available languages
        language_names_to_locales = {
            v: k for k, v in self.common.settings.available_locales.items()
        }
        language_names = list(language_names_to_locales)
        language_names.sort()
        for language_name in language_names:
            locale = language_names_to_locales[language_name]
            self.language_combobox.addItem(language_name, locale)
        language_layout = QtWidgets.QHBoxLayout()
        language_layout.addStretch()
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combobox)
        language_layout.addStretch()

        # Theme Settings
        theme_label = QtWidgets.QLabel(strings._("gui_settings_theme_label"))
        self.theme_combobox = QtWidgets.QComboBox()
        theme_choices = [
            strings._("gui_settings_theme_auto"),
            strings._("gui_settings_theme_light"),
            strings._("gui_settings_theme_dark"),
        ]
        self.theme_combobox.addItems(theme_choices)
        theme_layout = QtWidgets.QHBoxLayout()
        theme_layout.addStretch()
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combobox)
        theme_layout.addStretch()

        # Version and help
        version_label = QtWidgets.QLabel(
            strings._("gui_settings_version_label").format(self.common.version)
        )
        version_label.setAlignment(QtCore.Qt.AlignHCenter)
        help_label = QtWidgets.QLabel(strings._("gui_settings_help_label"))
        help_label.setAlignment(QtCore.Qt.AlignHCenter)
        help_label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        help_label.setOpenExternalLinks(True)

        # Buttons
        self.save_button = QtWidgets.QPushButton(strings._("gui_settings_button_save"))
        self.save_button.clicked.connect(self.save_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addStretch()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addStretch()
        layout.addWidget(autoupdate_widget)
        if autoupdate_widget.isVisible():
            layout.addSpacing(20)
        layout.addLayout(language_layout)
        layout.addLayout(theme_layout)
        layout.addSpacing(20)
        layout.addWidget(version_label)
        layout.addWidget(help_label)
        layout.addSpacing(20)
        layout.addLayout(buttons_layout)
        layout.addStretch()

        self.setLayout(layout)

        self.reload_settings()

        if self.common.gui.onion.connected_to_tor:
            self.tor_is_connected()
        else:
            self.tor_is_disconnected()

    def reload_settings(self):
        # Load settings, and fill them in
        self.old_settings = Settings(self.common)
        self.old_settings.load()

        use_autoupdate = self.old_settings.get("use_autoupdate")
        if use_autoupdate:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)

        autoupdate_timestamp = self.old_settings.get("autoupdate_timestamp")
        self._update_autoupdate_timestamp(autoupdate_timestamp)

        locale = self.old_settings.get("locale")
        locale_index = self.language_combobox.findData(locale)
        self.language_combobox.setCurrentIndex(locale_index)

        theme_choice = self.old_settings.get("theme")
        self.theme_combobox.setCurrentIndex(theme_choice)

    def check_for_updates(self):
        """
        Check for Updates button clicked. Manually force an update check.
        """
        self.common.log("SettingsTab", "check_for_updates")
        # Disable buttons
        self._disable_buttons()
        self.common.gui.qtapp.processEvents()

        def update_timestamp():
            # Update the last checked label
            settings = Settings(self.common)
            settings.load()
            autoupdate_timestamp = settings.get("autoupdate_timestamp")
            self._update_autoupdate_timestamp(autoupdate_timestamp)

        def close_forced_update_thread():
            forced_update_thread.quit()
            # Enable buttons
            self._enable_buttons()
            # Update timestamp
            update_timestamp()

        # Check for updates
        def update_available(update_url, installed_version, latest_version):
            Alert(
                self.common,
                strings._("update_available").format(
                    update_url, installed_version, latest_version
                ),
            )
            close_forced_update_thread()

        def update_not_available():
            Alert(self.common, strings._("update_not_available"))
            close_forced_update_thread()

        def update_error():
            Alert(
                self.common,
                strings._("update_error_check_error"),
                QtWidgets.QMessageBox.Warning,
            )
            close_forced_update_thread()

        def update_invalid_version(latest_version):
            Alert(
                self.common,
                strings._("update_error_invalid_latest_version").format(latest_version),
                QtWidgets.QMessageBox.Warning,
            )
            close_forced_update_thread()

        forced_update_thread = UpdateThread(
            self.common, self.common.gui.onion, force=True
        )
        forced_update_thread.update_available.connect(update_available)
        forced_update_thread.update_not_available.connect(update_not_available)
        forced_update_thread.update_error.connect(update_error)
        forced_update_thread.update_invalid_version.connect(update_invalid_version)
        forced_update_thread.start()

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        self.common.log("SettingsTab", "save_clicked")

        def changed(s1, s2, keys):
            """
            Compare the Settings objects s1 and s2 and return true if any values
            have changed for the given keys.
            """
            for key in keys:
                if s1.get(key) != s2.get(key):
                    return True
            return False

        settings = self.settings_from_fields()
        if settings:
            # If language changed, inform user they need to restart OnionShare
            if changed(settings, self.old_settings, ["locale"]):
                # Look up error message in different locale
                new_locale = settings.get("locale")
                if (
                    new_locale in strings.translations
                    and "gui_settings_language_changed_notice"
                    in strings.translations[new_locale]
                ):
                    notice = strings.translations[new_locale][
                        "gui_settings_language_changed_notice"
                    ]
                else:
                    notice = strings._("gui_settings_language_changed_notice")
                Alert(self.common, notice, QtWidgets.QMessageBox.Information)

            # If color mode changed, inform user they need to restart OnionShare
            if changed(settings, self.old_settings, ["theme"]):
                notice = strings._("gui_color_mode_changed_notice")
                Alert(self.common, notice, QtWidgets.QMessageBox.Information)

            # Save the new settings
            settings.save()
            self.parent.close_this_tab.emit()

    def help_clicked(self):
        """
        Help button clicked.
        """
        self.common.log("SettingsTab", "help_clicked")
        SettingsTab.open_help()

    @staticmethod
    def open_help():
        help_url = "https://docs.onionshare.org/"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_url))

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        self.common.log("SettingsTab", "settings_from_fields")
        settings = Settings(self.common)
        settings.load()  # To get the last update timestamp

        # Theme
        theme_index = self.theme_combobox.currentIndex()
        settings.set("theme", theme_index)

        # Language
        locale_index = self.language_combobox.currentIndex()
        locale = self.language_combobox.itemData(locale_index)
        settings.set("locale", locale)

        return settings

    def settings_have_changed(self):
        # Global settings have changed
        self.common.log("SettingsTab", "settings_have_changed")

    def _update_autoupdate_timestamp(self, autoupdate_timestamp):
        self.common.log("SettingsTab", "_update_autoupdate_timestamp")

        if autoupdate_timestamp:
            dt = datetime.datetime.fromtimestamp(autoupdate_timestamp)
            last_checked = dt.strftime("%B %d, %Y %H:%M")
        else:
            last_checked = strings._("gui_settings_autoupdate_timestamp_never")
        self.autoupdate_timestamp.setText(
            strings._("gui_settings_autoupdate_timestamp").format(last_checked)
        )

    def _disable_buttons(self):
        self.common.log("SettingsTab", "_disable_buttons")

        self.check_for_updates_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def _enable_buttons(self):
        self.common.log("SettingsTab", "_enable_buttons")
        # We can't check for updates if we're still not connected to Tor
        if not self.common.gui.onion.connected_to_tor:
            self.check_for_updates_button.setEnabled(False)
        else:
            self.check_for_updates_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def tor_is_connected(self):
        self.check_for_updates_button.show()

    def tor_is_disconnected(self):
        self.check_for_updates_button.hide()
