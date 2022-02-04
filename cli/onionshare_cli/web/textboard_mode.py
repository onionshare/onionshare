from flask import request, render_template, make_response, jsonify, session, redirect
from flask_socketio import emit, ConnectionRefusedError
from datetime import datetime
import uuid
import json
import os

# TODO: Refresh site more often, reduce cache lifetime
# TODO: rewrite ThreadPost to include self.textboard_dir on instance

class TextboardModeWeb:
    def __init__(self, common, web):
        self.common = common
        self.common.log("TextboardModeWeb", "__init__")

        self.web = web

        self.textboard_dir = self.web.settings.get("textboard", "data_dir")

        # This tracks the history id
        self.cur_history_id = 0

        # Whether or not we can send REQUEST_INDIVIDUAL_FILE_STARTED
        # and maybe other events when requests come in to this mode
        # Chat mode has no concept of individual file requests that
        # turn into history widgets in the GUI, so set it to False
        self.supports_file_requests = False

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for textboard
        """
        
        @self.web.app.route("/", methods=["GET"], provide_automatic_options=False)
        def index():
            history_id = self.cur_history_id
            self.cur_history_id += 1
            self.web.add_request(
                request.path,
                {"id": history_id, "status_code": 200},
            )

            self.web.add_request(self.web.REQUEST_LOAD, request.path)
            return render_template(
                    "textboard.html",
                    static_url_path=self.web.static_url_path,
                    title=self.web.settings.get("general", "title"),
                    threads=self.ThreadPost.load_threads_from_disk(self.textboard_dir),
            )
        
        @self.web.app.route("/create-thread", methods=["POST"], provide_automatic_options=False)
        def create_thread():
            content = request.form.get('content')
            # when content empty, don't make thread or something
            title = request.form.get('title')
            title = "" if title == None else title
            post_date = datetime.now().strftime("%d %b %Y %H:%M:%S") # dd mnth YYYY H:M:S
            #TODO: add timezone (datetime is naive)
            
            thread_id = uuid.uuid4().hex

            post = self.ThreadPost("thread", content, post_date, thread_id, title)
            post.save_to_file(thread_id, self.textboard_dir)
            return redirect(f'/thread/{thread_id}')
        
        @self.web.app.route("/thread/<string:thread_id>", methods=["GET"], provide_automatic_options=False)
        def thread_page(thread_id: str): #TODO: get GET parameter (which thread you replying to)
            return render_template(
                "textboard_thread.html",
                static_url_path=self.web.static_url_path,
                title=self.web.settings.get("general", "title"),
                thread=self.ThreadPost.load_thread_by_id(thread_id, self.textboard_dir),
                reply_to=request.args.get('reply', default = "", type = str),
            )
        
        @self.web.app.route("/thread-reply", methods=["POST"], provide_automatic_options=False)
        def thread_reply():
            content = request.form.get("content")
            post_date = datetime.now().strftime("%d %b %Y %H:%M:%S")
            thread_id = request.form.get('thread-id')

            post = self.ThreadPost("reply", content, post_date, self.ThreadPost.get_new_post_id(thread_id, self.textboard_dir))
            post.save_to_file(thread_id, self.textboard_dir)
            return redirect(f'/thread/{thread_id}')

    class ThreadPost:
        def __init__(self, post_type: str, content: str, post_date: str, post_id: str, title: str=""):
            self.post_type = post_type
            self.post_date = post_date
            self.content = content
            self.title = title
            self.post_id = post_id

        def save_to_file(self, thread_id: str, textboard_dir: str):
            thread_dir = os.path.join(textboard_dir, thread_id)
            thread_datafile = os.path.join(thread_dir, "data.json")

            post = {
                "date": self.post_date,
                "content": self.content,
                "id": self.post_id
            }
            if self.post_type == "thread":
                post["title"] = self.title
            
            if os.path.exists(thread_datafile): #just append post to list
                with open(thread_datafile, "r+") as f:
                    data = json.load(f)
                    print(data)
                    data.append(post)
                    print(data)
                    f.seek(0)
                    f.write(json.dumps(data))
            
            else: #create directories and data.json
                os.makedirs(thread_dir, 0o700)
                jsonpost = json.dumps([post])
                with open(thread_datafile, 'a') as f:
                    f.write(jsonpost)
        
        @classmethod
        def get_new_post_id(cls, thread_id: str, textboard_dir: str):
            thread = cls.load_thread_by_id(thread_id, textboard_dir)
            post_id = str(len(thread))
            return post_id

        @staticmethod
        def load_thread_by_id(id: str, textboard_dir: str):
            thread_datafile = os.path.join(textboard_dir, id, "data.json")
            if os.path.exists(thread_datafile):
                with open(thread_datafile, 'r') as f:
                    return json.load(f)

        @staticmethod
        def load_threads_from_disk(textboard_dir: str):
            threads=[]
            for root, dirs, files in os.walk(textboard_dir, topdown=False):
                if "data.json" in files:
                    thread_file = os.path.join(root, "data.json")
                    with open(thread_file, 'r') as f:
                        data = json.load(f)
                        threads.append(data)
            return threads