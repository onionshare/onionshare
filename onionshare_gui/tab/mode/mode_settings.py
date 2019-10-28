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
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


class ModeSettings(QtWidgets.QWidget):
    """
    A settings widget
    """

    change_persistent = QtCore.pyqtSignal(int, bool)

    def __init__(self, common, tab_id):
        super(ModeSettings, self).__init__()
        self.common = common
        self.tab_id = tab_id

        # Downstream Mode need to fill in this layout with its settings
        self.mode_specific_layout = QtWidgets.QVBoxLayout()

        # Persistent
        self.persistent_checkbox = QtWidgets.QCheckBox()
        self.persistent_checkbox.clicked.connect(self.persistent_checkbox_clicked)
        self.persistent_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.persistent_checkbox.setText(strings._("mode_settings_persistent_checkbox"))

        # Public
        self.public_checkbox = QtWidgets.QCheckBox()
        self.public_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.public_checkbox.setText(strings._("mode_settings_public_checkbox"))

        # Whether or not to use an auto-start timer
        self.autostart_timer_checkbox = QtWidgets.QCheckBox()
        self.autostart_timer_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.autostart_timer_checkbox.setText(
            strings._("mode_settings_autostart_timer_checkbox")
        )

        # Whether or not to use an auto-stop timer
        self.autostop_timer_checkbox = QtWidgets.QCheckBox()
        self.autostop_timer_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.autostop_timer_checkbox.setText(
            strings._("mode_settings_autostop_timer_checkbox")
        )

        # Legacy address
        self.legacy_checkbox = QtWidgets.QCheckBox()
        self.legacy_checkbox.clicked.connect(self.update_ui)
        self.legacy_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.legacy_checkbox.setText(strings._("mode_settings_legacy_checkbox"))

        # Client auth
        self.client_auth_checkbox = QtWidgets.QCheckBox()
        self.client_auth_checkbox.clicked.connect(self.update_ui)
        self.client_auth_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.client_auth_checkbox.setText(
            strings._("mode_settings_client_auth_checkbox")
        )

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
        advanced_layout.addWidget(self.public_checkbox)
        advanced_layout.addWidget(self.autostart_timer_checkbox)
        advanced_layout.addWidget(self.autostop_timer_checkbox)
        advanced_layout.addWidget(self.legacy_checkbox)
        advanced_layout.addWidget(self.client_auth_checkbox)
        self.advanced_widget = QtWidgets.QWidget()
        self.advanced_widget.setLayout(advanced_layout)
        self.advanced_widget.hide()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.mode_specific_layout)
        layout.addWidget(self.persistent_checkbox)
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

    def persistent_checkbox_clicked(self):
        self.change_persistent.emit(self.tab_id, self.persistent_checkbox.isChecked())

    def toggle_advanced_clicked(self):
        if self.advanced_widget.isVisible():
            self.advanced_widget.hide()
        else:
            self.advanced_widget.show()

        self.update_ui()
