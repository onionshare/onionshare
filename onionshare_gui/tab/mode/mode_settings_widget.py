# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

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
from PyQt5 import QtCore, QtWidgets

from onionshare import strings


class ModeSettingsWidget(QtWidgets.QWidget):
    """
    All of the common settings for each mode are in this widget
    """

    change_persistent = QtCore.pyqtSignal(int, bool)

    def __init__(self, common, tab, mode_settings):
        super(ModeSettingsWidget, self).__init__()
        self.common = common
        self.tab = tab
        self.settings = mode_settings

        # Downstream Mode need to fill in this layout with its settings
        self.mode_specific_layout = QtWidgets.QVBoxLayout()

        # Persistent
        self.persistent_checkbox = QtWidgets.QCheckBox()
        self.persistent_checkbox.clicked.connect(self.persistent_checkbox_clicked)
        self.persistent_checkbox.setText(strings._("mode_settings_persistent_checkbox"))
        if self.settings.get("persistent", "enabled"):
            self.persistent_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.persistent_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # Public
        self.public_checkbox = QtWidgets.QCheckBox()
        self.public_checkbox.clicked.connect(self.public_checkbox_clicked)
        self.public_checkbox.setText(strings._("mode_settings_public_checkbox"))
        if self.settings.get("general", "public"):
            self.public_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.public_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # Whether or not to use an auto-start timer
        self.autostart_timer_checkbox = QtWidgets.QCheckBox()
        self.autostart_timer_checkbox.clicked.connect(
            self.autostart_timer_checkbox_clicked
        )
        self.autostart_timer_checkbox.setText(
            strings._("mode_settings_autostart_timer_checkbox")
        )
        if self.settings.get("general", "autostart_timer"):
            self.autostart_timer_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autostart_timer_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # The autostart timer widget
        self.autostart_timer_widget = QtWidgets.QDateTimeEdit()
        self.autostart_timer_widget.setDisplayFormat("hh:mm A MMM d, yy")
        self.autostart_timer_reset()
        self.autostart_timer_widget.setCurrentSection(
            QtWidgets.QDateTimeEdit.MinuteSection
        )
        if self.settings.get("general", "autostart_timer"):
            self.autostart_timer_widget.show()
        else:
            self.autostart_timer_widget.hide()

        # Autostart timer layout
        autostart_timer_layout = QtWidgets.QHBoxLayout()
        autostart_timer_layout.setContentsMargins(0, 0, 0, 0)
        autostart_timer_layout.addWidget(self.autostart_timer_checkbox)
        autostart_timer_layout.addWidget(self.autostart_timer_widget)

        # Whether or not to use an auto-stop timer
        self.autostop_timer_checkbox = QtWidgets.QCheckBox()
        self.autostop_timer_checkbox.clicked.connect(
            self.autostop_timer_checkbox_clicked
        )
        self.autostop_timer_checkbox.setText(
            strings._("mode_settings_autostop_timer_checkbox")
        )
        if self.settings.get("general", "autostop_timer"):
            self.autostop_timer_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.autostop_timer_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # The autostop timer widget
        self.autostop_timer_widget = QtWidgets.QDateTimeEdit()
        self.autostop_timer_widget.setDisplayFormat("hh:mm A MMM d, yy")
        self.autostop_timer_reset()
        self.autostop_timer_widget.setCurrentSection(
            QtWidgets.QDateTimeEdit.MinuteSection
        )
        if self.settings.get("general", "autostop_timer"):
            self.autostop_timer_widget.show()
        else:
            self.autostop_timer_widget.hide()

        # Autostop timer layout
        autostop_timer_layout = QtWidgets.QHBoxLayout()
        autostop_timer_layout.setContentsMargins(0, 0, 0, 0)
        autostop_timer_layout.addWidget(self.autostop_timer_checkbox)
        autostop_timer_layout.addWidget(self.autostop_timer_widget)

        # Legacy address
        self.legacy_checkbox = QtWidgets.QCheckBox()
        self.legacy_checkbox.clicked.connect(self.legacy_checkbox_clicked)
        self.legacy_checkbox.clicked.connect(self.update_ui)
        self.legacy_checkbox.setText(strings._("mode_settings_legacy_checkbox"))
        if self.settings.get("general", "legacy"):
            self.legacy_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.legacy_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # Client auth
        self.client_auth_checkbox = QtWidgets.QCheckBox()
        self.client_auth_checkbox.clicked.connect(self.client_auth_checkbox_clicked)
        self.client_auth_checkbox.clicked.connect(self.update_ui)
        self.client_auth_checkbox.setText(
            strings._("mode_settings_client_auth_checkbox")
        )
        if self.settings.get("general", "client_auth"):
            self.client_auth_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.client_auth_checkbox.setCheckState(QtCore.Qt.Unchecked)

        # Toggle advanced settings
        self.toggle_advanced_button = QtWidgets.QPushButton()
        self.toggle_advanced_button.clicked.connect(self.toggle_advanced_clicked)
        self.toggle_advanced_button.setFlat(True)
        self.toggle_advanced_button.setStyleSheet(
            self.common.gui.css["mode_settings_toggle_advanced"]
        )

        # Advanced group itself
        advanced_layout = QtWidgets.QVBoxLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addLayout(autostart_timer_layout)
        advanced_layout.addLayout(autostop_timer_layout)
        advanced_layout.addWidget(self.legacy_checkbox)
        advanced_layout.addWidget(self.client_auth_checkbox)
        self.advanced_widget = QtWidgets.QWidget()
        self.advanced_widget.setLayout(advanced_layout)
        self.advanced_widget.hide()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.mode_specific_layout)
        layout.addWidget(self.persistent_checkbox)
        layout.addWidget(self.public_checkbox)
        layout.addWidget(self.advanced_widget)
        layout.addWidget(self.toggle_advanced_button)
        self.setLayout(layout)

        self.update_ui()

    def update_ui(self):
        # Update text on advanced group toggle button
        if self.advanced_widget.isVisible():
            self.toggle_advanced_button.setText(
                strings._("mode_settings_advanced_toggle_hide")
            )
        else:
            self.toggle_advanced_button.setText(
                strings._("mode_settings_advanced_toggle_show")
            )

        # Client auth is only a legacy option
        if self.client_auth_checkbox.isChecked():
            self.legacy_checkbox.setChecked(True)
            self.legacy_checkbox.setEnabled(False)
        else:
            self.legacy_checkbox.setEnabled(True)
        if self.legacy_checkbox.isChecked():
            self.client_auth_checkbox.show()
        else:
            self.client_auth_checkbox.hide()

        # If the server has been started in the past, prevent changing legacy option
        if self.settings.get("onion", "private_key"):
            if self.legacy_checkbox.isChecked():
                # If using legacy, disable legacy and client auth options
                self.legacy_checkbox.setEnabled(False)
                self.client_auth_checkbox.setEnabled(False)
            else:
                # If using v3, hide legacy and client auth options
                self.legacy_checkbox.hide()
                self.client_auth_checkbox.hide()

    def persistent_checkbox_clicked(self):
        self.settings.set("persistent", "enabled", self.persistent_checkbox.isChecked())
        self.settings.set("persistent", "mode", self.tab.mode)
        self.change_persistent.emit(
            self.tab.tab_id, self.persistent_checkbox.isChecked()
        )

        # If disabling persistence, delete the file from disk and remove any existing onion address details from settings
        if not self.persistent_checkbox.isChecked():
            self.settings.set("onion", "password", "")
            self.settings.set("onion", "private_key", "")
            self.settings.set("onion", "hidservauth_string", "")
            self.settings.delete()

    def public_checkbox_clicked(self):
        self.settings.set("general", "public", self.public_checkbox.isChecked())

    def autostart_timer_checkbox_clicked(self):
        self.settings.set(
            "general", "autostart_timer", self.autostart_timer_checkbox.isChecked()
        )

        if self.autostart_timer_checkbox.isChecked():
            self.autostart_timer_widget.show()
        else:
            self.autostart_timer_widget.hide()

    def autostop_timer_checkbox_clicked(self):
        self.settings.set(
            "general", "autostop_timer", self.autostop_timer_checkbox.isChecked()
        )

        if self.autostop_timer_checkbox.isChecked():
            self.autostop_timer_widget.show()
        else:
            self.autostop_timer_widget.hide()

    def legacy_checkbox_clicked(self):
        self.settings.set("general", "legacy", self.legacy_checkbox.isChecked())

    def client_auth_checkbox_clicked(self):
        self.settings.set(
            "general", "client_auth", self.client_auth_checkbox.isChecked()
        )

    def toggle_advanced_clicked(self):
        if self.advanced_widget.isVisible():
            self.advanced_widget.hide()
        else:
            self.advanced_widget.show()

        self.update_ui()

    def autostart_timer_reset(self):
        """
        Reset the auto-start timer in the UI after stopping a share
        """
        if self.common.gui.local_only:
            # For testing
            self.autostart_timer_widget.setDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(15)
            )
            self.autostart_timer_widget.setMinimumDateTime(
                QtCore.QDateTime.currentDateTime()
            )
        else:
            self.autostart_timer_widget.setDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(
                    300
                )  # 5 minutes in the future
            )
            self.autostart_timer_widget.setMinimumDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(60)
            )

    def autostop_timer_reset(self):
        """
        Reset the auto-stop timer in the UI after stopping a share
        """
        if self.common.gui.local_only:
            # For testing
            self.autostop_timer_widget.setDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(15)
            )
            self.autostop_timer_widget.setMinimumDateTime(
                QtCore.QDateTime.currentDateTime()
            )
        else:
            self.autostop_timer_widget.setDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(300)
            )
            self.autostop_timer_widget.setMinimumDateTime(
                QtCore.QDateTime.currentDateTime().addSecs(60)
            )
