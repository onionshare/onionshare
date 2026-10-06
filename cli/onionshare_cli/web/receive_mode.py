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
import os
import tempfile
import json
import requests
import io
from datetime import datetime
from flask import Request, request, render_template, make_response, flash, redirect
from werkzeug.exceptions import RequestEntityTooLarge
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

        # Running total of bytes received by this service, used when the
        # maximum upload size is applied to the service's entire lifespan. The
        # value is loaded from the mode settings so it survives restarts of a
        # persistent service, and persisted again as bytes are received.
        self.total_upload_size = self.web.settings.get("receive", "total_upload_size")

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

            max_upload_size = self.web.settings.get("receive", "max_upload_size")
            return render_template(
                "receive.html",
                static_url_path=self.web.static_url_path,
                disable_text=self.web.settings.get("receive", "disable_text"),
                disable_files=self.web.settings.get("receive", "disable_files"),
                title=self.web.settings.get("general", "title"),
                max_upload_size=max_upload_size,
                max_upload_size_human=(
                    self.web.common.human_readable_filesize(max_upload_size)
                    if max_upload_size
                    else None
                ),
                max_upload_size_total=self.web.settings.get(
                    "receive", "max_upload_size_total"
                ),
            )

        @self.web.app.route(
            "/upload", methods=["POST"], provide_automatic_options=False
        )
        def upload(ajax=False):
            """
            Handle the upload files POST request, though at this point, the files have
            already been uploaded and saved to their correct locations.
            """
            # /upload-ajax rejects these requests before dispatching here,
            # but plain (non-JS) form submissions hit this route directly.
            # Requests that were admitted before the autostop timer ran out
            # are allowed to finish normally, even if the timer expires
            # while they are in progress.
            if not request.admitted:
                if ajax:
                    return json.dumps(
                        {"error_flashes": ["Uploads are no longer being accepted"]}
                    )
                flash("Uploads are no longer being accepted", "error")
                return redirect("/")

            # Reject uploads that exceed the maximum size. This is normally
            # detected before the body is read, but Content-Length is not
            # trustworthy, so it can also be raised while streaming files.
            if request.total_upload_size_exceeded or request.upload_too_large:
                return self.upload_too_large_response(ajax)

            message_received = request.includes_message

            files_received = 0
            if not self.web.settings.get("receive", "disable_files"):
                try:
                    files = request.files.getlist("file[]")
                except RequestEntityTooLarge:
                    request.upload_too_large = True
                    return self.upload_too_large_response(ajax)

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
            else:
                # Check if files were submitted when disabled
                try:
                    files = request.files.getlist("file[]")
                except RequestEntityTooLarge:
                    request.upload_too_large = True
                    return self.upload_too_large_response(ajax)
                if files and any(f.filename != "" for f in files):
                    request.upload_error = True
                    if ajax:
                        return json.dumps(
                            {"error_flashes": ["File uploads are not allowed"]}
                        )
                    else:
                        flash("File uploads are not allowed", "error")
                        return redirect("/")

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
                    if not self.web.settings.get("receive", "disable_text"):
                        msg = "Nothing submitted or message was too long (> 524288 characters)"
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
                    return make_response(
                        render_template("thankyou.html"),
                        static_url_path=self.web.static_url_path,
                        title=self.web.settings.get("general", "title"),
                    )

        @self.web.app.route(
            "/upload-ajax", methods=["POST"], provide_automatic_options=False
        )
        def upload_ajax_public():
            if not request.admitted:
                return self.web.error403()
            return upload(ajax=True)

    def upload_too_large_response(self, ajax):
        """
        Reject an upload that exceeds the configured maximum size. Writes
        nothing, and tells the sender (and the GUI) what happened.
        """
        self.common.log(
            "ReceiveModeWeb", "upload_too_large_response", "upload too large"
        )
        self.web.add_request(
            self.web.REQUEST_UPLOAD_TOO_LARGE,
            request.path,
            {"history_id": request.history_id},
        )

        if request.total_upload_size_exceeded:
            msg = "This service has reached its maximum upload size"
        else:
            msg = "The file is too large to upload"

        # Show a user-facing message, so the CLI tool reports rejected uploads
        print(f"Upload rejected: {msg}")

        if ajax:
            return make_response(json.dumps({"error_flashes": [msg]}), 413)

        flash(msg, "error")
        return (
            render_template(
                "413.html",
                static_url_path=self.web.static_url_path,
                title=self.web.settings.get("general", "title"),
            ),
            413,
        )

    def add_upload_size(self, size):
        """
        Add to the running total of bytes received, so a service using the
        total upload size limit can refuse further uploads once it is reached.
        The total is persisted in the mode settings so it survives restarts of
        a persistent service.
        """
        if size <= 0:
            return

        self.total_upload_size += size
        self.web.settings.set("receive", "total_upload_size", self.total_upload_size)
        self.web.common.log(
            "ReceiveModeWeb",
            "add_upload_size",
            f"total upload size is now {self.total_upload_size} bytes",
        )

        if self.web.settings.get("receive", "max_upload_size_total"):
            max_upload_size = self.web.settings.get("receive", "max_upload_size")
            if max_upload_size > 0 and self.total_upload_size >= max_upload_size:
                self.can_upload = False
                self.web.common.log(
                    "ReceiveModeWeb",
                    "add_upload_size",
                    "service maximum upload size reached, refusing more uploads",
                )

    def send_webhook_notification(self, data):
        self.common.log("ReceiveModeWeb", "send_webhook_notification", data)
        try:
            self.web.requests_session.post(
                self.web.settings.get("receive", "webhook_url"),
                data=data,
                timeout=5,
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
        if (
            self.upload_error
            or self.onionshare_request.upload_too_large
            or (not self.onionshare_request.stop_q.empty())
        ):
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

        # Whether this upload request was admitted (started) before the
        # autostop timer expired. This is decided once, here, and used
        # consistently for the rest of the request's lifecycle, so that
        # an upload that was already in progress when the timer ran out
        # is allowed to finish normally.
        self.admitted = False

        if self.upload_request:
            self.web.common.log("ReceiveModeRequest", "__init__")

            # No errors yet
            self.upload_error = False
            self.file_upload_rejected = False
            self.upload_too_large = False
            self.total_upload_size_exceeded = False

            # Don't create directory yet - wait to see if there's actual content
            self.receive_mode_dir = None
            self.message_filename = None

            # A dictionary that maps filenames to the bytes uploaded so far
            self.progress = {}

            self.admitted = self.web.receive_mode.can_upload

            # These are used by close() even when the upload is refused
            self.history_id = None
            self.told_gui_about_request = False
            self.previous_file = None
            self.includes_message = False
            self.uploaded_bytes = 0
            self.content_length = 0
            self.effective_max_upload_size = 0

            # Figure out the content length. This is an untrusted header.
            try:
                self.content_length = int(self.headers["Content-Length"])
            except Exception:
                self.content_length = 0

            # Werkzeug 3.1 caps non-file form fields at 500000 bytes by
            # default, which is below OnionShare's documented 524288-character
            # text message limit. Allow enough bytes for that limit (a UTF-8
            # character is at most 4 bytes) so long messages aren't rejected.
            self.max_form_memory_size = 524288 * 4

            # Work out the maximum size allowed for this request. When the
            # maximum is applied to the service's entire lifespan, the
            # effective limit is whatever remains of the total budget. The
            # running total is loaded from the mode settings so it survives
            # restarts of a persistent service.
            self.max_upload_size = self.web.settings.get("receive", "max_upload_size")
            self.max_upload_size_total = self.web.settings.get(
                "receive", "max_upload_size_total"
            )
            if self.max_upload_size > 0:
                if self.max_upload_size_total:
                    remaining = (
                        self.max_upload_size - self.web.receive_mode.total_upload_size
                    )
                    if remaining <= 0:
                        self.total_upload_size_exceeded = True
                    else:
                        self.effective_max_upload_size = remaining
                else:
                    self.effective_max_upload_size = self.max_upload_size

            # Let Werkzeug cap the size of the whole request body. It raises
            # RequestEntityTooLarge preemptively when Content-Length is too
            # big, and while streaming when the server terminates the request
            # (e.g. chunked encoding). This is a ceiling on the request body,
            # which includes multipart overhead; the exact limit on received
            # file bytes is enforced in file_write_func().
            if self.max_upload_size > 0:
                self.max_content_length = self.max_upload_size

            # Fail closed before reading the body if we already know it is too
            # big. Content-Length is not trustworthy on its own, so the
            # streaming check in file_write_func() is the real guard.
            if self.total_upload_size_exceeded:
                self.upload_too_large = True
                self.web.common.log(
                    "ReceiveModeRequest",
                    "__init__",
                    "refusing upload: service total upload size reached",
                )
            elif (
                self.max_upload_size > 0 and self.content_length > self.max_upload_size
            ):
                self.upload_too_large = True
                self.web.common.log(
                    "ReceiveModeRequest",
                    "__init__",
                    "refusing upload: Content-Length exceeds maximum",
                )

            # Prevent new uploads if we've said so (timer expired), or if the
            # service has reached its total upload size.
            if self.admitted and not self.upload_too_large:

                # Create an history_id, attach it to the request
                self.history_id = self.web.receive_mode.cur_history_id
                self.web.receive_mode.cur_history_id += 1

                date_str = datetime.now().strftime("%b %d, %I:%M%p")
                size_str = self.web.common.human_readable_filesize(self.content_length)
                print(f"{date_str}: Upload of total size {size_str} is starting")

                # Is there a text message?
                if not self.web.settings.get("receive", "disable_text"):
                    try:
                        text_message = self.form.get("text")
                    except RequestEntityTooLarge:
                        # The body is too big, even though Content-Length did
                        # not say so (e.g. chunked encoding)
                        self.upload_too_large = True
                        self.web.common.log(
                            "ReceiveModeRequest",
                            "__init__",
                            "refusing upload: exceeded maximum while parsing",
                        )
                    else:
                        if text_message and len(text_message) <= 524288:
                            if text_message.strip() != "":
                                self.includes_message = True
                                # Create directory only if there's a message
                                self._create_receive_directory()
                                if not self.upload_error:
                                    self.message_filename = (
                                        f"{self.receive_mode_dir}-message.txt"
                                    )
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

    def _create_receive_directory(self):
        """
        Create the receive mode directory. Called only when there's actual content to save.
        """
        if self.receive_mode_dir is not None:
            return  # Already created

        now = datetime.now()
        date_dir = now.strftime("%Y-%m-%d")
        time_dir = now.strftime("%H%M%S%f")
        self.receive_mode_dir = os.path.join(
            self.web.settings.get("receive", "data_dir"), date_dir, time_dir
        )

        try:
            os.makedirs(self.receive_mode_dir, 0o700, exist_ok=False)
        except OSError:
            if os.path.exists(self.receive_mode_dir):
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
                    if i == 100:
                        self.web.common.log(
                            "ReceiveModeRequest",
                            "_create_receive_directory",
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
            print(f"Could not create OnionShare data folder: {self.receive_mode_dir}")
            self.web.common.log(
                "ReceiveModeRequest",
                "_create_receive_directory",
                "Permission denied creating receive mode directory",
            )
            self.upload_error = True

    def tell_gui_request_started(self):
        # Tell the GUI about the request
        if not self.told_gui_about_request:
            # Create directory if not already created (for file uploads)
            if self.receive_mode_dir is None and not self.upload_error:
                self._create_receive_directory()

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
        # Ignore empty file uploads (user didn't select a file)
        if not filename or filename.strip() == "":
            return io.BytesIO()

        if self.upload_request:
            # Reject uploads that were not admitted (autostop timer had
            # already expired when this request started), so nothing gets
            # saved to disk
            if not self.admitted:
                self.file_upload_rejected = True
                return io.BytesIO()

            # Reject the file stream if this request already exceeds the
            # maximum upload size, so nothing is written to disk
            if self.upload_too_large or self.total_upload_size_exceeded:
                self.web.common.log(
                    "ReceiveModeRequest",
                    "_get_file_stream",
                    "File upload rejected: exceeds maximum upload size",
                )
                self.file_upload_rejected = True
                return io.BytesIO()

            # Check if file uploads are disabled - reject file streams early
            if self.web.settings.get("receive", "disable_files"):
                self.web.common.log(
                    "ReceiveModeRequest",
                    "_get_file_stream",
                    "File upload rejected: disable_files is enabled",
                )
                self.file_upload_rejected = True
                return io.BytesIO()

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

            # Add to the service's running total of received bytes, so a
            # lifespan limit can refuse further uploads. Only count requests
            # that were accepted.
            if (
                not self.upload_error
                and not self.upload_too_large
                and not self.total_upload_size_exceeded
            ):
                self.web.receive_mode.add_upload_size(self.uploaded_bytes)

            # Clean up the receive mode directory:
            # - a request that exceeded the maximum size is thrown away entirely
            # - if no files were written, delete the empty directory
            # - if file uploads were rejected, delete the directory, keeping a
            #   valid message if one was submitted
            if self.receive_mode_dir is not None and os.path.isdir(
                self.receive_mode_dir
            ):
                try:
                    if self.upload_too_large or self.total_upload_size_exceeded:
                        # Reject the whole request: remove any partial files so
                        # a rejected upload cannot fill the disk
                        for filename in os.listdir(self.receive_mode_dir):
                            try:
                                os.remove(os.path.join(self.receive_mode_dir, filename))
                            except OSError:
                                pass
                        os.rmdir(self.receive_mode_dir)
                    elif (
                        len(os.listdir(self.receive_mode_dir)) == 0
                        or self.file_upload_rejected
                    ):
                        # Only delete if there are no actual files (messages are valid)
                        files = os.listdir(self.receive_mode_dir)
                        if len(files) == 0:
                            os.rmdir(self.receive_mode_dir)
                        elif (
                            self.file_upload_rejected
                            and len(files) == 1
                            and files[0].endswith("-message.txt")
                        ):
                            # File upload was rejected and only a message file exists
                            os.remove(os.path.join(self.receive_mode_dir, files[0]))
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
            self.uploaded_bytes += length

            # Enforce the maximum upload size while writing. Content-Length is
            # untrusted, so this is the real guard against oversized uploads.
            if (
                not self.upload_too_large
                and self.effective_max_upload_size > 0
                and self.uploaded_bytes > self.effective_max_upload_size
            ):
                self.upload_too_large = True
                self.web.common.log(
                    "ReceiveModeRequest",
                    "file_write_func",
                    "upload exceeded the maximum size, cancelling",
                )

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
