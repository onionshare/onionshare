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
from onionshare import strings
from onionshare.onion import Onion


class GuiCommon:
    """
    The shared code for all of the OnionShare GUI.
    """

    MODE_SHARE = "share"
    MODE_RECEIVE = "receive"
    MODE_WEBSITE = "website"

    def __init__(self, common, qtapp, local_only, config):
        self.common = common
        self.qtapp = qtapp
        self.local_only = local_only

        # Load settings, if a custom config was passed in
        self.config = config
        if self.config:
            self.common.load_settings(self.config)
        else:
            self.common.load_settings()

        # Load strings
        strings.load_strings(self.common)

        # Start the Onion
        self.onion = Onion(common)

        self.css = {
            # OnionShareGui styles
            "tab_bar_new_tab": """
                QTabBar::tab:last {
                    border: 0;
                    margin: 3px;
                }""",
            "tab_bar_new_tab_button": """
                QToolButton {
                    font-weight: bold;
                    font-size: 20px;
                }""",
            "new_tab_button": """
                QPushButton {
                    font-weight: bold;
                    font-size: 30px;
                    color: #601f61;
                }""",
            "mode_switcher_selected_style": """
                QPushButton {
                    color: #ffffff;
                    background-color: #4e064f;
                    border: 0;
                    border-right: 1px solid #69266b;
                    font-weight: bold;
                    border-radius: 0;
                }""",
            "mode_switcher_unselected_style": """
                QPushButton {
                    color: #ffffff;
                    background-color: #601f61;
                    border: 0;
                    font-weight: normal;
                    border-radius: 0;
                }""",
            "settings_button": """
                QPushButton {
                    background-color: #601f61;
                    border: 0;
                    border-left: 1px solid #69266b;
                    border-radius: 0;
                }""",
            "server_status_indicator_label": """
                QLabel {
                    font-style: italic;
                    color: #666666;
                    padding: 2px;
                }""",
            "status_bar": """
                QStatusBar {
                    font-style: italic;
                    color: #666666;
                }
                QStatusBar::item {
                    border: 0px;
                }""",
            # Common styles between modes and their child widgets
            "mode_info_label": """
                QLabel {
                    font-size: 12px;
                    color: #666666;
                }
                """,
            "server_status_url": """
                QLabel {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 10px;
                    border: 1px solid #666666;
                    font-size: 12px;
                }
                """,
            "server_status_url_buttons": """
                QPushButton {
                    color: #3f7fcf;
                }
                """,
            "server_status_button_stopped": """
                QPushButton {
                    background-color: #5fa416;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                }""",
            "server_status_button_working": """
                QPushButton {
                    background-color: #4c8211;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                    font-style: italic;
                }""",
            "server_status_button_started": """
                QPushButton {
                    background-color: #d0011b;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                }""",
            "downloads_uploads_empty": """
                QWidget {
                    background-color: #ffffff;
                    border: 1px solid #999999;
                }
                QWidget QLabel {
                    background-color: none;
                    border: 0px;
                }
                """,
            "downloads_uploads_empty_text": """
                QLabel {
                    color: #999999;
                }""",
            "downloads_uploads_label": """
                QLabel {
                    font-weight: bold;
                    font-size 14px;
                    text-align: center;
                    background-color: none;
                    border: none;
                }""",
            "downloads_uploads_clear": """
                QPushButton {
                    color: #3f7fcf;
                }
                """,
            "download_uploads_indicator": """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 2px;
                    border-radius: 7px;
                    text-align: center;
                }""",
            "downloads_uploads_progress_bar": """
                QProgressBar {
                    border: 1px solid #4e064f;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                    font-size: 14px;
                }
                QProgressBar::chunk {
                    background-color: #4e064f;
                    width: 10px;
                }""",
            "history_individual_file_timestamp_label": """
                QLabel {
                    color: #666666;
                }""",
            "history_individual_file_status_code_label_2xx": """
                QLabel {
                    color: #008800;
                }""",
            "history_individual_file_status_code_label_4xx": """
                QLabel {
                    color: #cc0000;
                }""",
            # Share mode and child widget styles
            "share_zip_progess_bar": """
                QProgressBar {
                    border: 1px solid #4e064f;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                }
                QProgressBar::chunk {
                    border: 0px;
                    background-color: #4e064f;
                    width: 10px;
                }""",
            "share_filesize_warning": """
                QLabel {
                    padding: 10px 0;
                    font-weight: bold;
                    color: #333333;
                }
                """,
            "share_file_selection_drop_here_label": """
                QLabel {
                    color: #999999;
                }""",
            "share_file_selection_drop_count_label": """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 10px;
                }""",
            "share_file_list_drag_enter": """
                FileList {
                    border: 3px solid #538ad0;
                }
                """,
            "share_file_list_drag_leave": """
                FileList {
                    border: none;
                }
                """,
            "share_file_list_item_size": """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",
            # Receive mode and child widget styles
            "receive_file": """
                QWidget {
                    background-color: #ffffff;
                }
                """,
            "receive_file_size": """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",
            # Settings dialog
            "settings_version": """
                QLabel {
                    color: #666666;
                }""",
            "settings_tor_status": """
                QLabel {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 10px;
                }""",
            "settings_whats_this": """
                QLabel {
                    font-size: 12px;
                }""",
            "settings_connect_to_tor": """
                QLabel {
                    font-style: italic;
                }""",
        }
