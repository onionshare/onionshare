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

import json
import os
import random
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
                        os.path.join(
                            "images", f"{common.gui.color_mode}_logo_text_bg.png"
                        )
                    )
                )
            )
        )
        self.image_label.setFixedSize(322, 65)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.image_label)
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # First launch widget
        self.first_launch_widget = AutoConnectFirstLaunchWidget(self.common)
        self.first_launch_widget.toggle_auto_connect.connect(self.toggle_auto_connect)
        self.first_launch_widget.connect_clicked.connect(
            self.first_launch_widget_connect_clicked
        )
        self.first_launch_widget.open_tor_settings.connect(self.open_tor_settings)
        self.first_launch_widget.show()

        # Use bridge widget
        self.use_bridge_widget = AutoConnectUseBridgeWidget(self.common)
        self.use_bridge_widget.connect_clicked.connect(self.use_bridge_connect_clicked)
        self.use_bridge_widget.back_clicked.connect(self.back_clicked)
        self.use_bridge_widget.open_tor_settings.connect(self.open_tor_settings)
        self.use_bridge_widget.hide()

        # Tor connection widget
        self.tor_con = TorConnectionWidget(self.common, self.status_bar)
        self.tor_con.success.connect(self.tor_con_success)
        self.tor_con.fail.connect(self.tor_con_fail)
        self.tor_con.hide()

        # Layout
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.addStretch()
        content_layout.addWidget(self.image)
        content_layout.addWidget(self.first_launch_widget)
        content_layout.addWidget(self.use_bridge_widget)
        content_layout.addWidget(self.tor_con)
        content_layout.addStretch()
        content_layout.setAlignment(QtCore.Qt.AlignCenter)
        content_widget = QtWidgets.QWidget()
        content_widget.setLayout(content_layout)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(content_widget)
        self.layout.addStretch()

        self.setLayout(self.layout)

    def check_autoconnect(self):
        """
        After rendering, check if autoconnect was clicked, then start connecting
        """
        self.common.log("AutoConnectTab", "autoconnect_checking")
        if self.auto_connect_enabled:
            self.first_launch_widget.enable_autoconnect_checkbox.setCheckState(
                QtCore.Qt.Checked
            )
            self.first_launch_widget_connect_clicked()

    def toggle_auto_connect(self):
        """
        Auto connect checkbox clicked
        """
        self.common.log("AutoConnectTab", "autoconnect_checkbox_clicked")
        self.curr_settings.set(
            "auto_connect",
            self.first_launch_widget.enable_autoconnect_checkbox.isChecked(),
        )
        self.curr_settings.save()

    def open_tor_settings(self):
        self.parent.open_tor_settings_tab()

    def first_launch_widget_connect_clicked(self):
        """
        Connect button in first launch widget clicked. Try to connect to tor.
        """
        self.common.log("AutoConnectTab", "first_launch_widget_connect_clicked")
        self.first_launch_widget.hide_buttons()

        if not self.common.gui.local_only:
            self.tor_con.show()
            self.tor_con.start(self.curr_settings)
        else:
            self.close_this_tab.emit()

    def use_bridge_connect_clicked(self):
        """
        Connect button in use bridge widget clicked.
        """
        self.common.log(
            "AutoConnectTab",
            "use_bridge_connect_clicked",
            "Trying to automatically obtain bridges",
        )
        self.use_bridge_widget.hide_buttons()
        self.use_bridge_widget.start_autodetecting_location()

        # self.common.gui.meek.start()
        # self.censorship_circumvention = CensorshipCircumvention(
        #     self.common, self.common.gui.meek
        # )
        # bridge_settings = self.censorship_circumvention.request_settings(country="tm")
        # self.common.gui.meek.cleanup()

        # if bridge_settings and self.censorship_circumvention.save_settings(
        #     self.settings, bridge_settings
        # ):
        #     # Try and connect again
        #     self.start()
        # else:
        #     self.fail.emit()

    def back_clicked(self):
        """
        Switch from use bridge widget back to first launch widget
        """
        self.use_bridge_widget.hide()
        self.first_launch_widget.show()

    def tor_con_success(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.first_launch_widget.show_buttons()
        self.use_bridge_widget.show_buttons()

        if self.common.gui.onion.is_authenticated() and not self.tor_con.wasCanceled():
            # Tell the tabs that Tor is connected
            self.tor_is_connected.emit()
            # Close the tab
            self.close_this_tab.emit()

    def tor_con_fail(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()

        # If we're on first launch, switch to use bridge
        if self.first_launch_widget.isVisible():
            self.first_launch_widget.show_buttons()
            self.first_launch_widget.hide()
            self.use_bridge_widget.show()


class AutoConnectFirstLaunchWidget(QtWidgets.QWidget):
    """
    When you first launch OnionShare, this is the widget that is displayed
    """

    toggle_auto_connect = QtCore.Signal()
    connect_clicked = QtCore.Signal()
    open_tor_settings = QtCore.Signal()

    def __init__(self, common):
        super(AutoConnectFirstLaunchWidget, self).__init__()
        self.common = common
        self.common.log("AutoConnectFirstLaunchWidget", "__init__")

        # Description and checkbox
        description_label = QtWidgets.QLabel(strings._("gui_autoconnect_description"))
        description_label.setWordWrap(True)
        self.enable_autoconnect_checkbox = ToggleCheckbox(
            strings._("gui_enable_autoconnect_checkbox")
        )
        self.enable_autoconnect_checkbox.clicked.connect(self._toggle_auto_connect)
        self.enable_autoconnect_checkbox.setFixedWidth(400)
        self.enable_autoconnect_checkbox.setStyleSheet(
            common.gui.css["enable_autoconnect"]
        )
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addWidget(description_label)
        description_layout.addWidget(self.enable_autoconnect_checkbox)
        description_widget = QtWidgets.QWidget()
        description_widget.setLayout(description_layout)

        # Buttons
        self.connect_button = QtWidgets.QPushButton(strings._("gui_autoconnect_start"))
        self.connect_button.clicked.connect(self._connect_clicked)
        self.connect_button.setFixedWidth(150)
        self.connect_button.setStyleSheet(common.gui.css["autoconnect_start_button"])
        self.configure_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_configure")
        )
        self.configure_button.clicked.connect(self._open_tor_settings)
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
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(description_widget)
        layout.addWidget(cta_widget)
        self.setLayout(layout)

    def hide_buttons(self):
        self.connect_button.hide()
        self.configure_button.hide()

    def show_buttons(self):
        self.connect_button.show()
        self.configure_button.show()

    def _toggle_auto_connect(self):
        self.toggle_auto_connect.emit()

    def _connect_clicked(self):
        self.connect_clicked.emit()

    def _open_tor_settings(self):
        self.open_tor_settings.emit()


class AutoConnectUseBridgeWidget(QtWidgets.QWidget):
    """
    If connecting fails, this is the widget that helps the user bypass censorship
    """

    connect_clicked = QtCore.Signal()
    back_clicked = QtCore.Signal()
    open_tor_settings = QtCore.Signal()

    def __init__(self, common):
        super(AutoConnectUseBridgeWidget, self).__init__()
        self.common = common
        self.common.log("AutoConnectUseBridgeWidget", "__init__")

        # Description
        description_label = QtWidgets.QLabel(
            strings._("gui_autoconnect_bridge_description")
        )
        description_label.setTextFormat(QtCore.Qt.RichText)
        description_label.setWordWrap(True)

        # Detection preference
        self.detect_automatic_radio = QtWidgets.QRadioButton(
            strings._("gui_autoconnect_bridge_detect_automatic")
        )
        self.detect_automatic_radio.toggled.connect(self._detect_automatic_toggled)
        self.detect_manual_radio = QtWidgets.QRadioButton(
            strings._("gui_autoconnect_bridge_detect_manual")
        )
        self.detect_manual_radio.toggled.connect(self._detect_manual_toggled)
        detect_layout = QtWidgets.QVBoxLayout()
        detect_layout.addWidget(self.detect_automatic_radio)
        detect_layout.addWidget(self.detect_manual_radio)

        # Country list
        locale = self.common.settings.get("locale")
        if not locale:
            locale = "en"

        with open(
            GuiCommon.get_resource_path(os.path.join("countries", f"{locale}.json"))
        ) as f:
            countries = json.loads(f.read())

        self.country_combobox = QtWidgets.QComboBox()
        self.country_combobox.setStyleSheet(
            common.gui.css["autoconnect_countries_combobox"]
        )
        for country_code in countries:
            self.country_combobox.addItem(countries[country_code], country_code)

        # Task label
        self.task_label = QtWidgets.QLabel()
        self.task_label.setStyleSheet(common.gui.css["enable_autoconnect"])
        self.task_label.hide()

        # Buttons
        self.connect_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_bridge_start")
        )
        self.connect_button.clicked.connect(self._connect_clicked)
        self.connect_button.setFixedWidth(150)
        self.connect_button.setStyleSheet(common.gui.css["autoconnect_start_button"])
        self.back_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_bridge_back")
        )
        self.back_button.clicked.connect(self._back_clicked)
        self.back_button.setFlat(True)
        self.back_button.setStyleSheet(common.gui.css["autoconnect_configure_button"])
        self.configure_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_configure")
        )
        self.configure_button.clicked.connect(self._open_tor_settings)
        self.configure_button.setFlat(True)
        self.configure_button.setStyleSheet(
            common.gui.css["autoconnect_configure_button"]
        )
        cta_layout = QtWidgets.QHBoxLayout()
        cta_layout.addWidget(self.connect_button)
        cta_layout.addWidget(self.back_button)
        cta_layout.addWidget(self.configure_button)
        cta_layout.addStretch()
        cta_widget = QtWidgets.QWidget()
        cta_widget.setLayout(cta_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(description_label)
        layout.addLayout(detect_layout)
        layout.addWidget(self.country_combobox)
        layout.addWidget(self.task_label)
        layout.addWidget(cta_widget)
        self.setLayout(layout)

        self.detect_automatic_radio.setChecked(True)

    def hide_buttons(self):
        self.connect_button.hide()
        self.back_button.hide()
        self.configure_button.hide()

    def show_buttons(self):
        self.connect_button.show()
        self.back_button.show()
        self.configure_button.show()

    def start_autodetecting_location(self):
        self.detect_automatic_radio.setEnabled(False)
        self.detect_manual_radio.setEnabled(False)

        self.country_combobox.setEnabled(False)
        self.country_combobox.show()

        # If we're automatically detecting it, randomly switch up the country
        # dropdown until we detect the location
        if self.detect_automatic_radio.isChecked():
            self.task_label.show()
            self.task_label.setText(strings._("gui_autoconnect_task_detect_location"))

            self.autodetecting_timer = QtCore.QTimer()
            self.autodetecting_timer.timeout.connect(self._autodetecting_timer_callback)
            self.autodetecting_timer.start(200)

    def stop_autodetecting_location(self):
        self.task_label.hide()
        self.autodetecting_timer.stop()

    def _autodetecting_timer_callback(self):
        new_index = random.randrange(0, self.country_combobox.count())
        self.country_combobox.setCurrentIndex(new_index)

    def _detect_automatic_toggled(self):
        self.country_combobox.setEnabled(False)
        self.country_combobox.hide()

    def _detect_manual_toggled(self):
        self.country_combobox.setEnabled(True)
        self.country_combobox.show()

    def _connect_clicked(self):
        self.connect_clicked.emit()

    def _back_clicked(self):
        self.back_clicked.emit()

    def _open_tor_settings(self):
        self.open_tor_settings.emit()
