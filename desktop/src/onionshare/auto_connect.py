# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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

from onionshare_cli.settings import Settings

from .gui_common import GuiCommon


class AutoConnect(QtWidgets.QWidget):
    """
    GUI window that appears in the very beginning to ask user if
    should auto connect.
    """
    def __init__(self, common, parent=None):
        super(AutoConnect, self).__init__(parent)
        common.log("AutoConnect", "__init__")

        # Was auto connected?
        self.curr_settings = Settings(common)
        self.curr_settings.load()
        self.auto_connect_enabled = self.curr_settings.get("auto_connect")

        if self.auto_connect_enabled:
            self.parent().start_onionshare()
        else:
            # Onionshare logo
            self.image_label = QtWidgets.QLabel()
            self.image_label.setPixmap(
                QtGui.QPixmap.fromImage(
                    QtGui.QImage(
                        GuiCommon.get_resource_path(
                            "images/{}_logo_text.png".format(common.gui.color_mode)
                        )
                    )
                )
            )
            self.image_label.setFixedSize(180, 40)
            image_layout = QtWidgets.QVBoxLayout()
            image_layout.addWidget(self.image_label)
            self.image = QtWidgets.QWidget()
            self.image.setLayout(image_layout)

            # Description and checkbox
            description_label = QtWidgets.QLabel("Some description about OnionShare and explain autoconnect stuff")
            self.enable_autoconnect_checkbox = QtWidgets.QCheckBox() 
            self.enable_autoconnect_checkbox.clicked.connect(self.toggle_auto_connect)
            self.enable_autoconnect_checkbox.setText(
                "Enable automatically connecting to OnionShare"
            )

            # CTA buttons
            self.connect_button = QtWidgets.QPushButton("Start OnionShare")
            self.connect_button.setStyleSheet(
                common.gui.css["server_status_button_stopped"]
            )
            self.configure_button = QtWidgets.QPushButton("Configure")
            cta_layout = QtWidgets.QHBoxLayout()
            cta_layout.addWidget(self.connect_button)
            cta_layout.addWidget(self.configure_button)
            cta_widget = QtWidgets.QWidget()
            cta_widget.setLayout(cta_layout)


            # Layout
            self.layout = QtWidgets.QVBoxLayout()
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.addStretch()
            self.layout.addWidget(self.image)
            self.layout.addWidget(description_label)
            self.layout.addWidget(self.enable_autoconnect_checkbox)
            self.layout.addStretch()
            self.layout.addWidget(cta_widget)
            self.layout.addStretch()
            self.layout.setAlignment(QtCore.Qt.AlignCenter)
            self.setLayout(self.layout)

    def toggle_auto_connect(self):
        self.curr_settings.set(
            "auto_connect", self.enable_autoconnect_checkbox.isChecked()
        )
        self.curr_settings.save()
