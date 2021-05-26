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

import os
import tempfile
import json
import requests
from datetime import datetime
from flask import Request, request, render_template, make_response, flash, redirect
from werkzeug.utils import secure_filename

# Receive mode uses a special flask requests object, ReceiveModeRequest, in
# order to keep track of upload progress. Here's what happens when someone
# uploads files:
# - new ReceiveModeRequest object is created
# - ReceiveModeRequest.__init__
#   - creates a directory based on the timestamp
#   - creates empty self.progress = dict, which will map uploaded files to their upload progress
# - ReceiveModeRequest._get_file_stream
#   - called for each file that gets upload
#   - the first time, send REQUEST_STARTED to GUI, and append to self.web.receive_mode.uploads_in_progress
#   - updates self.progress[self.filename] for the current file
#   - uses custom ReceiveModeFile to save file to disk
#   - ReceiveModeRequest.file_write_func called on each write
#     - Display progress in CLI, and send REQUEST_PROGRESS to GUI
#   - ReceiveModeRequest.file_close_func called when each file closes
#     - self.progress[filename]["complete"] = True
#  - ReceiveModeRequest.close
#     - send either REQUEST_UPLOAD_CANCELED or REQUEST_UPLOAD_FINISHED to GUI
#     - remove from self.web.receive_mode.uploads_in_progress


class ReceiveModeWeb:
    """
    All of the web logic for receive mode
    """

    def __init__(self, common, web):
        self.common = common
        self.common.log("ReceiveModeWeb", "__init__")

        self.web = web

        self.can_upload = True
        self.uploads_in_progress = []

        # This tracks the history id
        self.cur_history_id = 0

        # Whether or not we can send REQUEST_INDIVIDUAL_FILE_STARTED
        # and maybe other events when requests come in to this mode
        self.supports_file_requests = True

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for receiving files
        """

        @self.web.app.route("/", methods=["GET"], provide_automatic_options=False)
        def index():
            history_id = self.cur_history_id
            self.cur_history_id += 1
            self.web.add_request(
                self.web.REQUEST_INDIVIDUAL_FILE_STARTED,
                request.path,
                {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            r = make_response(
                render_template(
                    "receive.html",
                    static_url_path=self.web.static_url_path,
                    disable_text=self.web.settings.get("receive", "disable_text"),
                    disable_files=self.web.settings.get("receive", "disable_files"),
                    title=self.web.settings.get("general", "title"),
                )
            )
            return self.web.add_security_headers(r)

        @self.web.app.route("/upload", methods=["POST"], provide_automatic_options=False)
        def upload(ajax=False):
            """
            Handle the upload files POST request, though at this point, the files have
            already been uploaded and saved to their correct locations.
            """
            message_received = request.includes_message

            files_received = 0
            if not self.web.settings.get("receive", "disable_files"):
                files = request.files.getlist("file[]")

                filenames = []
                for f in files:
                    if f.filename != "":
                        filename = secure_filename(f.filename)
                        filenames.append(filename)
                        local_path = os.path.join(request.receive_mode_dir, filename)
                        basename = os.path.basename(local_path)

                        # Tell the GUI the receive mode directory for this file
                        self.web.add_request(
                            self.web.REQUEST_UPLOAD_SET_DIR,
                            request.path,
                            {
                                "id": request.history_id,
                                "filename": basename,
                                "dir": request.receive_mode_dir,
                            },
                        )

                        self.common.log(
                            "ReceiveModeWeb",
                            "define_routes",
                            f"/upload, uploaded {f.filename}, saving to {local_path}",
                        )
                        print(f"Received: {local_path}")

                files_received = len(filenames)

            # Send webhook if configured
            if (
                self.web.settings.get("receive", "webhook_url") is not None
                and not request.upload_error
                and (message_received or files_received)
            ):
                msg = ""
                if files_received > 0:
                    if files_received == 1:
                        msg += "1 file"
                    else:
                        msg += f"{files_received} files"
                if message_received:
                    if msg == "":
                        msg = "A text message"
                    else:
                        msg += " and a text message"
                self.send_webhook_notification(f"{msg} submitted to OnionShare")

            if request.upload_error:
                self.common.log(
                    "ReceiveModeWeb",
                    "define_routes",
                    "/upload, there was an upload error",
                )

                self.web.add_request(
                    self.web.REQUEST_ERROR_DATA_DIR_CANNOT_CREATE,
                    request.path,
                    {"receive_mode_dir": request.receive_mode_dir},
                )
                print(
                    f"Could not create OnionShare data folder: {request.receive_mode_dir}"
                )

                msg = "Error uploading, please inform the OnionShare user"
                if ajax:
                    return json.dumps({"error_flashes": [msg]})
                else:
                    flash(msg, "error")
                    return redirect("/")

            if ajax:
                info_flashes = []

            if files_received > 0:
                files_msg = ""
                for filename in filenames:
                    files_msg += f"{filename}, "
                files_msg = files_msg.rstrip(", ")

            if message_received:
                if files_received > 0:
                    msg = f"Message submitted, uploaded {files_msg}"
                else:
                    msg = "Message submitted"
            else:
                if files_received > 0:
                    msg = f"Uploaded {files_msg}"
                else:
                    msg = "Nothing submitted"

            if ajax:
                info_flashes.append(msg)
            else:
                flash(msg, "info")

            if self.can_upload:
                if ajax:
                    return json.dumps({"info_flashes": info_flashes})
                else:
                    return redirect("/")
            else:
                if ajax:
                    return json.dumps(
                        {
                            "new_body": render_template(
                                "thankyou.html",
                                static_url_path=self.web.static_url_path,
                                title=self.web.settings.get("general", "title"),
                            )
                        }
                    )
                else:
                    # It was the last upload and the timer ran out
                    r = make_response(
                        render_template("thankyou.html"),
                        static_url_path=self.web.static_url_path,
                        title=self.web.settings.get("general", "title"),
                    )
                    return self.web.add_security_headers(r)

        @self.web.app.route("/upload-ajax", methods=["POST"], provide_automatic_options=False)
        def upload_ajax_public():
            if not self.can_upload:
                return self.web.error403()
            return upload(ajax=True)

    def send_webhook_notification(self, data):
        self.common.log("ReceiveModeWeb", "send_webhook_notification", data)
        try:
            requests.post(
                self.web.settings.get("receive", "webhook_url"),
                data=data,
                timeout=5,
                proxies=self.web.proxies,
            )
        except Exception as e:
            print(f"Webhook notification failed: {e}")


class ReceiveModeWSGIMiddleware(object):
    """
    Custom WSGI middleware in order to attach the Web object to environ, so
    ReceiveModeRequest can access it.
    """

    def __init__(self, app, web):
        self.app = app
        self.web = web

    def __call__(self, environ, start_response):
        environ["web"] = self.web
        environ["stop_q"] = self.web.stop_q
        return self.app(environ, start_response)


class ReceiveModeFile(object):
    """
    A custom file object that tells ReceiveModeRequest every time data gets
    written to it, in order to track the progress of uploads. It starts out with
    a .part file extension, and when it's complete it removes that extension.
    """

    def __init__(self, request, filename, write_func, close_func):
        self.onionshare_request = request
        self.onionshare_filename = filename
        self.onionshare_write_func = write_func
        self.onionshare_close_func = close_func

        self.filename = os.path.join(self.onionshare_request.receive_mode_dir, filename)
        self.filename_in_progress = f"{self.filename}.part"

        # Open the file
        self.upload_error = False
        try:
            self.f = open(self.filename_in_progress, "wb+")
        except Exception:
            # This will only happen if someone is messing with the data dir while
            # OnionShare is running, but if it does make sure to throw an error
            self.upload_error = True
            self.f = tempfile.TemporaryFile("wb+")

        # Make all the file-like methods and attributes actually access the
        # TemporaryFile, except for write
        attrs = [
            "closed",
            "detach",
            "fileno",
            "flush",
            "isatty",
            "mode",
            "name",
            "peek",
            "raw",
            "read",
            "read1",
            "readable",
            "readinto",
            "readinto1",
            "readline",
            "readlines",
            "seek",
            "seekable",
            "tell",
            "truncate",
            "writable",
            "writelines",
        ]
        for attr in attrs:
            setattr(self, attr, getattr(self.f, attr))

    def write(self, b):
        """
        Custom write method that calls out to onionshare_write_func
        """
        if self.upload_error or (not self.onionshare_request.stop_q.empty()):
            self.close()
            self.onionshare_request.close()
            return

        try:
            bytes_written = self.f.write(b)
            self.onionshare_write_func(self.onionshare_filename, bytes_written)

        except Exception:
            self.upload_error = True

    def close(self):
        """
        Custom close method that calls out to onionshare_close_func
        """
        try:
            self.f.close()

            if not self.upload_error:
                # Rename the in progress file to the final filename
                os.rename(self.filename_in_progress, self.filename)

        except Exception:
            self.upload_error = True

        self.onionshare_close_func(self.onionshare_filename, self.upload_error)


class ReceiveModeRequest(Request):
    """
    A custom flask Request object that keeps track of how much data has been
    uploaded for each file, for receive mode.
    """

    def __init__(self, environ, populate_request=True, shallow=False):
        super(ReceiveModeRequest, self).__init__(environ, populate_request, shallow)
        self.web = environ["web"]
        self.stop_q = environ["stop_q"]
        self.filename = None

        # Prevent running the close() method more than once
        self.closed = False

        # Is this a valid upload request?
        self.upload_request = False
        if self.method == "POST":
            if self.path == "/upload" or self.path == "/upload-ajax":
                self.upload_request = True

        if self.upload_request:
            self.web.common.log("ReceiveModeRequest", "__init__")

            # No errors yet
            self.upload_error = False

            # Figure out what files should be saved
            now = datetime.now()
            date_dir = now.strftime("%Y-%m-%d")
            time_dir = now.strftime("%H%M%S")
            self.receive_mode_dir = os.path.join(
                self.web.settings.get("receive", "data_dir"), date_dir, time_dir
            )

            # Create that directory, which shouldn't exist yet
            try:
                os.makedirs(self.receive_mode_dir, 0o700, exist_ok=False)
            except OSError:
                # If this directory already exists, maybe someone else is uploading files at
                # the same second, so use a different name in that case
                if os.path.exists(self.receive_mode_dir):
                    # Keep going until we find a directory name that's available
                    i = 1
                    while True:
                        new_receive_mode_dir = f"{self.receive_mode_dir}-{i}"
                        try:
                            os.makedirs(new_receive_mode_dir, 0o700, exist_ok=False)
                            self.receive_mode_dir = new_receive_mode_dir
                            break
                        except OSError:
                            pass
                        i += 1
                        # Failsafe
                        if i == 100:
                            self.web.common.log(
                                "ReceiveModeRequest",
                                "__init__",
                                "Error finding available receive mode directory",
                            )
                            self.upload_error = True
                            break
            except PermissionError:
                self.web.add_request(
                    self.web.REQUEST_ERROR_DATA_DIR_CANNOT_CREATE,
                    request.path,
                    {"receive_mode_dir": self.receive_mode_dir},
                )
                print(
                    f"Could not create OnionShare data folder: {self.receive_mode_dir}"
                )
                self.web.common.log(
                    "ReceiveModeRequest",
                    "__init__",
                    "Permission denied creating receive mode directory",
                )
                self.upload_error = True

            # Figure out the message filename, in case there is a message
            self.message_filename = f"{self.receive_mode_dir}-message.txt"

            # If there's an error so far, finish early
            if self.upload_error:
                return

            # A dictionary that maps filenames to the bytes uploaded so far
            self.progress = {}

            # Prevent new uploads if we've said so (timer expired)
            if self.web.receive_mode.can_upload:

                # Create an history_id, attach it to the request
                self.history_id = self.web.receive_mode.cur_history_id
                self.web.receive_mode.cur_history_id += 1

                # Figure out the content length
                try:
                    self.content_length = int(self.headers["Content-Length"])
                except Exception:
                    self.content_length = 0

                date_str = datetime.now().strftime("%b %d, %I:%M%p")
                size_str = self.web.common.human_readable_filesize(self.content_length)
                print(f"{date_str}: Upload of total size {size_str} is starting")

                # Don't tell the GUI that a request has started until we start receiving files
                self.told_gui_about_request = False

                self.previous_file = None

                # Is there a text message?
                self.includes_message = False
                if not self.web.settings.get("receive", "disable_text"):
                    text_message = self.form.get("text")
                    if text_message:
                        if text_message.strip() != "":
                            self.includes_message = True

                            with open(self.message_filename, "w") as f:
                                f.write(text_message)

                            self.web.common.log(
                                "ReceiveModeRequest",
                                "__init__",
                                f"saved message to {self.message_filename}",
                            )
                            print(f"Received: {self.message_filename}")

                            # Tell the GUI about the message
                            self.tell_gui_request_started()
                            self.web.common.log(
                                "ReceiveModeRequest",
                                "__init__",
                                "sending REQUEST_UPLOAD_INCLUDES_MESSAGE to GUI",
                            )
                            self.web.add_request(
                                self.web.REQUEST_UPLOAD_INCLUDES_MESSAGE,
                                self.path,
                                {
                                    "id": self.history_id,
                                    "filename": self.message_filename,
                                },
                            )

    def tell_gui_request_started(self):
        # Tell the GUI about the request
        if not self.told_gui_about_request:
            self.web.common.log(
                "ReceiveModeRequest",
                "tell_gui_request_started",
                "sending REQUEST_STARTED to GUI",
            )
            self.web.add_request(
                self.web.REQUEST_STARTED,
                self.path,
                {
                    "id": self.history_id,
                    "content_length": self.content_length,
                },
            )
            self.web.receive_mode.uploads_in_progress.append(self.history_id)

            self.told_gui_about_request = True

    def _get_file_stream(
        self, total_content_length, content_type, filename=None, content_length=None
    ):
        """
        This gets called for each file that gets uploaded, and returns an file-like
        writable stream.
        """
        if self.upload_request:
            self.tell_gui_request_started()

            self.filename = secure_filename(filename)

            self.progress[self.filename] = {"uploaded_bytes": 0, "complete": False}

        f = ReceiveModeFile(
            self, self.filename, self.file_write_func, self.file_close_func
        )
        if f.upload_error:
            self.web.common.log(
                "ReceiveModeRequest", "_get_file_stream", "Error creating file"
            )
            self.upload_error = True
        return f

    def close(self):
        """
        Closing the request.
        """
        super(ReceiveModeRequest, self).close()

        # Prevent calling this method more than once per request
        if self.closed:
            return
        self.closed = True

        if self.upload_request:
            self.web.common.log("ReceiveModeRequest", "close")

            if self.told_gui_about_request:
                history_id = self.history_id

                if not self.web.stop_q.empty() or (
                    self.filename in self.progress
                    and not self.progress[self.filename]["complete"]
                ):
                    # Inform the GUI that the upload has canceled
                    self.web.common.log(
                        "ReceiveModeRequest",
                        "close",
                        "sending REQUEST_UPLOAD_CANCELED to GUI",
                    )
                    self.web.add_request(
                        self.web.REQUEST_UPLOAD_CANCELED,
                        self.path,
                        {"id": history_id},
                    )
                else:
                    # Inform the GUI that the upload has finished
                    self.web.common.log(
                        "ReceiveModeRequest",
                        "close",
                        "sending REQUEST_UPLOAD_FINISHED to GUI",
                    )
                    self.web.add_request(
                        self.web.REQUEST_UPLOAD_FINISHED,
                        self.path,
                        {"id": history_id},
                    )
                self.web.receive_mode.uploads_in_progress.remove(history_id)

            # If no files were written to self.receive_mode_dir, delete it
            try:
                if len(os.listdir(self.receive_mode_dir)) == 0:
                    os.rmdir(self.receive_mode_dir)
            except Exception:
                pass

    def file_write_func(self, filename, length):
        """
        This function gets called when a specific file is written to.
        """
        if self.closed:
            return

        if self.upload_request:
            self.progress[filename]["uploaded_bytes"] += length

            if self.previous_file != filename:
                self.previous_file = filename

            size_str = self.web.common.human_readable_filesize(
                self.progress[filename]["uploaded_bytes"]
            )

            if self.web.common.verbose:
                print(f"=> {size_str} {filename}")
            else:
                print(f"\r=> {size_str} {filename}          ", end="")

            # Update the GUI on the upload progress
            if self.told_gui_about_request:
                self.web.add_request(
                    self.web.REQUEST_PROGRESS,
                    self.path,
                    {"id": self.history_id, "progress": self.progress},
                )

    def file_close_func(self, filename, upload_error=False):
        """
        This function gets called when a specific file is closed.
        """
        self.progress[filename]["complete"] = True

        # If the file tells us there was an upload error, let the request know as well
        if upload_error:
            self.upload_error = True
