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

from . import strings
from .gui_common import GuiCommon, ToggleCheckbox
from .tor_connection import TorConnectionWidget


class AutoConnectTab(QtWidgets.QWidget):
    """
    Initial Tab that appears in the very beginning to ask user if
    should auto connect.
    """

    close_this_tab = QtCore.Signal()
    tor_is_connected = QtCore.Signal()
    tor_is_disconnected = QtCore.Signal()
    def __init__(self, common, tab_id, status_bar, parent=None):
        super(AutoConnectTab, self).__init__()
        self.common = common
        self.common.log("AutoConnectTab", "__init__")

        self.status_bar = status_bar
        self.tab_id = tab_id
        self.parent = parent

        # Was auto connected?
        self.curr_settings = Settings(common)
        self.curr_settings.load()
        self.auto_connect_enabled = self.curr_settings.get("auto_connect")

        # Onionshare logo
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(
                        "images/{}_logo_text_bg.png".format(common.gui.color_mode)
                    )
                )
            )
        )
        self.image_label.setFixedSize(322, 65)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.image_label)
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # Description and checkbox
        description_label = QtWidgets.QLabel(strings._("gui_autoconnect_description"))
        self.enable_autoconnect_checkbox = ToggleCheckbox(
            strings._("gui_enable_autoconnect_checkbox")
        ) 
        self.enable_autoconnect_checkbox.clicked.connect(self.toggle_auto_connect)
        # self.enable_autoconnect_checkbox.setText(
        #     strings._("gui_enable_autoconnect_checkbox")
        # )
        self.enable_autoconnect_checkbox.setFixedWidth(400)
        self.enable_autoconnect_checkbox.setStyleSheet(
            common.gui.css["enable_autoconnect"]
        )
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addWidget(description_label)
        description_layout.addWidget(self.enable_autoconnect_checkbox)
        description_widget = QtWidgets.QWidget()
        description_widget.setLayout(description_layout)

        # Tor connection widget
        self.tor_con = TorConnectionWidget(self.common, self.status_bar)
        self.tor_con.success.connect(self.tor_con_success)
        self.tor_con.fail.connect(self.tor_con_fail)
        self.tor_con.hide()

        # Error label
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet(self.common.gui.css["tor_settings_error"])
        self.error_label.setWordWrap(True)

        # CTA buttons
        self.connect_button = QtWidgets.QPushButton(strings._("gui_autoconnect_start"))
        self.connect_button.clicked.connect(self.connect_clicked)
        self.connect_button.setFixedWidth(150)
        self.connect_button.setStyleSheet(
            common.gui.css["autoconnect_start_button"]
        )
        self.configure_button = QtWidgets.QPushButton(strings._("gui_autoconnect_configure"))
        self.configure_button.clicked.connect(self.open_tor_settings)
        self.configure_button.setFlat(True)
        self.configure_button.setStyleSheet(
            common.gui.css["autoconnect_configure_button"]
        )
        cta_layout = QtWidgets.QHBoxLayout()
        cta_layout.addWidget(self.connect_button)
        cta_layout.addWidget(self.configure_button)
        cta_widget = QtWidgets.QWidget()
        cta_widget.setLayout(cta_layout)


        # Layout
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.addStretch()
        content_layout.addWidget(self.image)
        content_layout.addWidget(description_widget)
        content_layout.addWidget(self.tor_con)
        content_layout.addWidget(cta_widget)
        content_layout.addStretch()
        content_layout.setAlignment(QtCore.Qt.AlignCenter)
        content_widget = QtWidgets.QWidget()
        content_widget.setLayout(content_layout)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(content_widget)
        self.layout.addStretch()

        self.setLayout(self.layout)

        if self.auto_connect_enabled:
            self.connect_clicked()

    def toggle_auto_connect(self):
        """
        Auto connect checkbox clicked
        """
        self.common.log("AutoConnectTab", "autoconnect_checkbox_clicked")
        self.curr_settings.set(
            "auto_connect", self.enable_autoconnect_checkbox.isChecked()
        )
        self.curr_settings.save()

    def open_tor_settings(self):
        self.parent.open_tor_settings_tab()

    def connect_clicked(self):
        """
        Connect button clicked. Try to connect to tor.
        """
        self.common.log("AutoConnectTab", "connect_clicked")

        self.error_label.setText("")
        self.connect_button.hide()
        self.configure_button.hide()

        if not self.common.gui.local_only:
            self.tor_con.show()
            self.tor_con.start(self.curr_settings)
        else:
            self.close_this_tab.emit()

    def tor_con_success(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.connect_button.show()
        self.configure_button.show()
        if (
            self.common.gui.onion.is_authenticated()
            and not self.tor_con.wasCanceled()
        ):
            # Tell the tabs that Tor is connected
            self.tor_is_connected.emit()
            # Close the tab
            self.close_this_tab.emit()

    def tor_con_fail(self, msg):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.connect_button.show()
        self.configure_button.show()
        self.error_label.setText(msg)
