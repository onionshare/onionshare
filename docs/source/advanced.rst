Advanced Usage
==============

.. _save_tabs:

Save Tabs
---------

Closing OnionShare tabs you host destroys them, preventing reuse.
Persistently hosted websites are available on the same address even if the computer they are shared from is rebooted.

Make any tab persistent by checking the "Always open this tab when OnionShare is started" box before starting your server.

.. image:: _static/screenshots/advanced-save-tabs.png

When opening OnionShare, your saved tabs from the prior session will start opened.
Each service then can be started manually, and will be available on the same OnionShare address and be protected by the same private key.

If you save a tab, a copy of its onion service secret key is stored on your computer.

.. _turn_off_private_key:

Turn Off Private Key
--------------------

By default, all OnionShare services are protected with a private key, which Tor calls "client authentication".

The Tor Browser will ask you to enter your private key when you load an OnionShare service.
If you want to allow the public to use your service, it's better to disable the private key altogether.

To turn off the private key for any tab, check the "This is a public OnionShare service (disables private key)" box before starting the server.
Then the server will be public and a private key is not needed to load it in the Tor Browser.

.. _custom_titles:

Custom Titles
-------------

When people load OnionShare services in the Tor Browser they see the default title for each type of service.
For example, the default title for chat services is "OnionShare Chat".

If you edit the "Custom title" setting before starting a server you can change it.

Scheduled Times
---------------

OnionShare supports scheduling exactly when a service should start and stop.
Before starting a server, click "Show advanced settings" in its tab and then check the boxes next to either
"Start onion service at scheduled time", "Stop onion service at scheduled time", or both, and set the respective desired dates and times.

Services scheduled to start in the future display a countdown timer when the "Start sharing" button is clicked.
Services scheduled to stop in the future display a countdown timer when started.

**Scheduling an OnionShare service to automatically start can be used as a dead man's switch**.
This means your service is made public at a given time in the future if you are not there to prevent it.
If nothing happens to you, you can cancel the service before it's scheduled to start.

.. image:: _static/screenshots/advanced-schedule-start-timer.png

**Scheduling an OnionShare service to automatically stop limits its exposure**.
If you want to share secret info or something that will be outdated, you can do so for selected limited time.

.. image:: _static/screenshots/advanced-schedule-stop-timer.png

.. _cli:

Command-line Interface
----------------------

In addition to its graphical interface, OnionShare has a command-line interface.

Installing the CLI version
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have installed the Snap, macOS or Windows package, you already have the CLI version installed.

Alternatively, you can install just the command-line version of OnionShare using ``pip3``::

    pip3 install --user onionshare-cli

Note that you will also need the ``tor`` package installed. In macOS, install it with: ``brew install tor``

Then run it like this::

    onionshare-cli --help

Info about installing it on different operating systems can be found in the `CLI README file <https://github.com/onionshare/onionshare/blob/develop/cli/README.md>`_ in the Git repository.

Running the CLI from Snap
^^^^^^^^^^^^^^^^^^^^^^^^^

If you installed OnionShare using the Snap package, you can run ``onionshare.cli`` to access the command-line interface version.

Running the CLI from macOS
^^^^^^^^^^^^^^^^^^^^^^^^^^

From Terminal, you can run ``/Applications/OnionShare.app/Contents/MacOS/onionshare-cli --help``

Running the CLI from Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the Windows installation, the executable ``onionshare-cli.exe`` is available.

Usage
^^^^^

Browse the command-line documentation by running ``onionshare --help``::

    $ onionshare-cli --help
    ╭───────────────────────────────────────────╮
    │    *            ▄▄█████▄▄            *    │
    │               ▄████▀▀▀████▄     *         │
    │              ▀▀█▀       ▀██▄              │
    │      *      ▄█▄          ▀██▄             │
    │           ▄█████▄         ███        -+-  │
    │             ███         ▀█████▀           │
    │             ▀██▄          ▀█▀             │
    │         *    ▀██▄       ▄█▄▄     *        │
    │ *             ▀████▄▄▄████▀               │
    │                 ▀▀█████▀▀                 │
    │             -+-                     *     │
    │   ▄▀▄               ▄▀▀ █                 │
    │   █ █     ▀         ▀▄  █                 │
    │   █ █ █▀▄ █ ▄▀▄ █▀▄  ▀▄ █▀▄ ▄▀▄ █▄▀ ▄█▄   │
    │   ▀▄▀ █ █ █ ▀▄▀ █ █ ▄▄▀ █ █ ▀▄█ █   ▀▄▄   │
    │                                           │
    │                  v2.4.1                   │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯

    usage: onionshare-cli [-h] [--receive] [--website] [--chat] [--local-only] [--connect-timeout SECONDS] [--config FILENAME] [--persistent FILENAME] [--title TITLE] [--public]
                          [--auto-start-timer SECONDS] [--auto-stop-timer SECONDS] [--no-autostop-sharing] [--log-filenames] [--qr] [--data-dir data_dir] [--webhook-url webhook_url] [--disable-text]
                          [--disable-files] [--disable_csp] [--custom_csp custom_csp] [-v]
                          [filename ...]

    positional arguments:
      filename                  List of files or folders to share

    optional arguments:
      -h, --help                Show this help message and exit
      --receive                 Receive files
      --website                 Publish website
      --chat                    Start chat server
      --local-only              Don't use Tor (only for development)
      --connect-timeout SECONDS
                                Give up connecting to Tor after a given amount of seconds (default: 120)
      --config FILENAME         Filename of custom global settings
      --persistent FILENAME     Filename of persistent session
      --title TITLE             Set a title
      --public                  Don't use a private key
      --auto-start-timer SECONDS
                                Start onion service at scheduled time (N seconds from now)
      --auto-stop-timer SECONDS
                                Stop onion service at scheduled time (N seconds from now)
      --no-autostop-sharing     Share files: Continue sharing after files have been sent (the default is to stop sharing)
      --log-filenames           Log file download activity to stdout
      --qr                      Display a QR code in the terminal for share links
      --data-dir data_dir       Receive files: Save files received to this directory
      --webhook-url webhook_url
                                Receive files: URL to receive webhook notifications
      --disable-text            Receive files: Disable receiving text messages
      --disable-files           Receive files: Disable receiving files
      --disable_csp             Publish website: Disable the default Content Security Policy header (allows your website to use third-party resources)
      --custom_csp custom_csp   Publish website: Set a custom Content Security Policy header
      -v, --verbose             Log OnionShare errors to stdout, and web errors to disk


Running the CLI as a systemd unit file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to automatically start OnionShare from the CLI using a systemd unit file.

You may find this particularly useful if you are operating in 'persistent' mode, and want to start the same onion service every time your machine starts.

To do this, you need to prepare some OnionShare json config first.

Here is the main OnionShare config. In this example, it's stored in ``/home/user/.config/onionshare/onionshare.json``. You may need to adjust some of the settings, but if you already have OnionShare installed, it probably looks much like this already::

    {
      "version": "2.6.2",
      "connection_type": "bundled",
      "control_port_address": "127.0.0.1",
      "control_port_port": 9051,
      "socks_address": "127.0.0.1",
      "socks_port": 9050,
      "socket_file_path": "/var/run/tor/control",
      "auth_type": "no_auth",
      "auth_password": "",
      "auto_connect": true,
      "use_autoupdate": true,
      "autoupdate_timestamp": null,
      "bridges_enabled": false,
      "bridges_type": "built-in",
      "bridges_builtin_pt": "obfs4",
      "bridges_moat": "",
      "bridges_custom": "",
      "bridges_builtin": {},
      "persistent_tabs": [
          "my-persistent-onion"
      ],
      "locale": "en",
      "theme": 0
    }


Notice the 'persistent_tabs' section. We will now create a file at ``/home/user/.config/onionshare/persistent/my-persistent-onion.json``, that looks like this::

    {
      "onion": {
          "private_key": "UDIaZD8QgoXRP8JnAJ+pnlogQazfZ0wrfWJk5zPBGUBqg6+lozzjUJKTYWxwrxR33pDgJdTFtCUN1CX1FE22UQ==",
          "client_auth_priv_key": "RHJSN4VI3NKGDSIWK45CCWTLYOJHA6DQQRQXUID3FXMAILYXWVUQ",
          "client_auth_pub_key": "J4YLYAHS25UU3TZTE27H32RN3MCRGLR345U52XS2JNQ76CCHCRSQ"
      },
      "persistent": {
          "mode": "share",
          "enabled": true
      },
      "general": {
          "title": null,
          "public": false,
          "autostart_timer": 0,
          "autostop_timer": 0,
          "service_id": "niktadkcp6z7rym3r5o3j2hnmis53mno5ughvur357xo7jkjvmqrchid",
          "qr": false
      },
      "share": {
         "autostop_sharing": true,
         "filenames": [
           "/home/user/my-shared-file.txt"
         ]
      },
      "receive": {
         "data_dir": "/home/user/OnionShare",
         "webhook_url": null,
         "disable_text": false,
         "disable_files": false
      },
      "website": {
         "disable_csp": false,
         "custom_csp": null,
         "filenames": []
      },
      "chat": {}
    }

**Don't actually use this private key, service_id or client_auth keys! They are shown only as an example. Never share the private_key with anyone.**

The easiest way to generate the onion address and private key is to first create a 'pinned' OnionShare tab in the desktop app and started the share for the first time. This will then have saved the persistent settings to your ``.config/onionshare/persistent/`` folder with a random name. You can unpin that tab once you've generated it the first time. Or, you can leave it where it is, and use that persistent file in your systemd unit file below.

Now you can create a systemd unit file in ``/etc/systemd/system/onionshare-cli.service``. Be sure to adjust the User and Group to your own user/group, as well as changes to any paths to the onionshare-cli binary or the paths to your JSON configs and shares.

The systemd unit file should look like this::

    [Unit]
    Description=OnionShare CLI
    After=network.target

    [Service]
    ExecStart=/home/user/.local/bin/onionshare-cli --persistent /home/user/.config/onionshare/persistent/my-persistent-onion.json /home/user/my-shared-file.txt
    Restart=on-failure
    User=user
    Group=user

    [Install]
    WantedBy=multi-user.target

Note that although ``/home/user/my-shared-file.txt`` was defined in the ``filenames`` section of the ``my-persistent-onion.json`` file, it's still necessary to specify it as the argument to the onionshare-cli command.

Be sure to run ``sudo systemctl daemon-reload`` after creating the unit file.

Now you can run ``sudo systemctl start onionshare-cli.service``. If you have ``journalctl`` installed, you can run ``sudo journalctl -f -t onionshare-cli``, and you should see some output of your service starting::

    [...]
    Feb 09 10:14:09 onionshare onionshare-cli[18852]: [6.5K blob data]
    Feb 09 10:14:18 onionshare onionshare-cli[18852]: Compressing files.
    Feb 09 10:14:18 onionshare onionshare-cli[18852]: Give this address and private key to the recipient:
    Feb 09 10:14:18 onionshare onionshare-cli[18852]: http://niktadkcp6z7rym3r5o3j2hnmis53mno5ughvur357xo7jkjvmqrchid.onion
    Feb 09 10:14:18 onionshare onionshare-cli[18852]: Private key: RHJSN4VI3NKGDSIWK45CCWTLYOJHA6DQQRQXUID3FXMAILYXWVUQ
    Feb 09 10:14:18 onionshare onionshare-cli[18852]: Press Ctrl+C to stop the server

If you don't want your users to use a Private Key, set ``public`` to be ``true`` in the ``general`` settings of the my-persistent-onion.json file.


Keyboard Shortcuts
------------------

The OnionShare desktop application contains some keyboard shortcuts, for convenience and accessibility::

    Ctrl T - New Tab
    Ctrl X - Closes current tab

And from the main mode chooser screen::

    Ctrl S - Share mode
    Ctrl R - Receive mode
    Ctrl W - Website mode
    Ctrl C - Chat mode
    Ctrl H - Settings tab


Migrating your OnionShare data to another computer
--------------------------------------------------

You may want to migrate your OnionShare data when switching to another computer. This is especially true if you had a 'persistent' onion address and you want to preserve it.

OnionShare stores all such data in a specific folder. Copy the relevant folder for your operating system below, to your new computer:

 * Linux: ``~/.config/onionshare``
 * macOS: ``~/Library/Application Support/OnionShare``
 * Windows: ``%APPDATA%\OnionShare``


Configuration file parameters
-----------------------------

OnionShare stores its settings in a JSON file. Both the CLI and the Desktop versions use this configuration file. The CLI also lets you specify a path to a custom configuration file with ``--config``.

Below are the configuration file parameters and what they mean. If your configuration file has other parameters not listed here, they may be obsolete from older OnionShare versions.

==================== =========== ===========
Parameter            Type        Explanation
==================== =========== ===========
version              ``string``  The version of OnionShare. You should not ever need to change this value.
connection_type      ``string``  The way in which OnionShare connects to Tor. Valid options are 'bundled', 'automatic' (use Tor Browser's Tor connection), 'control_port' or 'socket_file'. Default: 'bundled'
control_port_address ``string``  The IP address of Tor's Control port, if ``connection_type`` is set to 'control_port'. Default: '127.0.0.1'
control_port_port    ``integer`` The port number of Tor's Control port, if ``connection_type`` is set to 'control_port'. Default: '9051'
socks_address        ``string``  The IP address of Tor's SOCKS proxy, if ``connection_type`` is set to 'control_port' or 'socket_file'. Default: '127.0.0.1'
socks_port           ``integer`` The port number of Tor's SOCKS proxy, if ``connection_type`` is set to 'control_port' or 'socket_file'. Default: '127.0.0.1'
socket_file_path     ``string``  The path to Tor's socket file, if ``connection_type`` is set to 'socket_file'. Default: '/var/run/tor/control'
auth_type            ``string``  If access to Tor's control port requires a password, this can be set to 'password', otherwise 'no_auth'. Default: 'no_auth'
auth_password        ``string``  If access to Tor's control port requires a password, and ``auth_type`` is set to 'password', specify the password here. Default: ''
auto_connect         ``boolean`` Whether OnionShare should automatically connect to Tor when it starts. Default: False
use_autoupdate       ``boolean`` Whether OnionShare should automatically check for updates (over Tor). This setting is only valid for MacOS or Windows installations. Default: True.
autoupdate_timestamp ``integer`` The last time OnionShare checked for updates. Default: None
bridges_enabled      ``boolean`` Whether to connect to Tor using bridges. Default: False
bridges_type         ``string``  When ``bridges_enabled`` is True, where to load bridges from. Options are "built-in" (bridges shipped with OnionShare and which may get updated from Tor), "moat" (request bridges from Tor's Moat API), or "custom" (user-supplied bridges). Default: "built-in"
bridges_builtin_pt   ``string``  When ``bridges_type`` is set to "built-in", this specifies which type of bridge protocol to use. Options are "obfs4", "meek-azure" or "snowflake". Default: "obfs4"
bridges_moat         ``string``  When ``bridges_type`` is set to "moat", the bridges returned from Tor's Moat API are stored here. Default: ""
bridges_custom       ``string``  When ``bridges_type`` is set to "custom", the bridges specified by the user are stored here. Separate each bridge line in the string with '\n'. Default: ""
bridges_builtin      ``dict``    When ``bridges_type`` is set to "built-in", OnionShare obtains the latest built-in bridges recommended by Tor and stores them here. Default: {}
persistent_tabs      ``list``    If the user has defined any tabs as 'saved' (meaning that they are persistent each time OnionShare starts, and their onion address doesn't change), these are given a random identifier which gets listed here. The persistent onion is stored as a JSON file with the same name as this identifier, in a subfolder of the OnionShare configuration folder called 'persistent'. Default: []
locale               ``string``  The locale used in OnionShare. Default: None (which is the same as 'en'). For valid locale codes, see 'available_locales' in https://github.com/onionshare/onionshare/blob/main/cli/onionshare_cli/settings.py
theme                ``boolean`` The theme for the OnionShare desktop app. Valid options are 0 (automatically detect the user's computer's light or dark theme), 1 (light) or 2 (dark).
==================== =========== ===========


Configuration file parameters for persistent onions
---------------------------------------------------

As described above, each 'persistent' onion has parameters of its own which are stored in its own JSON file. The path to this file can be specified for the CLI tool with ``--persistent``.

Here is an example persistent JSON configuration::

    {
      "onion": {
          "private_key": "0HGxILDDwYhxAB2Zq8mM3Wu3MirBgK7Fw2/tVrTw1XraElH7MWbVn3lzKbcJEapVWz2TFjaoCAVN48hGqraiRg==",
          "client_auth_priv_key": "UT55HDBA5VSRWOUERMGOHEIBKZCMOOGZAFFNI54GDQFZ6CMCUGIQ",
          "client_auth_pub_key": "TPQCMCV26UEDMCWGZCWAWM4FOJSQKZZTVPC5TC3CAGMDWKV255OA"
      },
      "persistent": {
          "mode": "share",
          "enabled": true,
          "autostart_on_launch": false
      },
      "general": {
          "title": null,
          "public": false,
          "autostart_timer": false,
          "autostop_timer": false,
          "service_id": "hvsufvk2anyadehahfqiacy4wbrjt2atpnagk4itlkh4mdfsg6vhd5ad"
      },
      "share": {
          "autostop_sharing": true,
          "filenames": [
              "/home/user/git/onionshare/desktop/org.onionshare.OnionShare.svg"
          ],
          "log_filenames": false
      },
      "receive": {
          "data_dir": "/home/user/OnionShare",
          "webhook_url": null,
          "disable_text": false,
          "disable_files": false
      },
      "website": {
          "disable_csp": false,
          "custom_csp": null,
          "log_filenames": false,
          "filenames": []
      },
      "chat": {}
    }


Below are the configuration file parameters for a persistent onion and what they mean, for each section in the JSON

onion
^^^^^

==================== ========== ===========
Parameter            Type       Explanation
==================== ========== ===========
private_key          ``string`` Base64-encoded private key of the onion service
client_auth_priv_key ``string`` The private key when using Client Authentication. Send this to the user.
client_auth_pub_key  ``string`` The public key when using Client Authentication. Used on OnionShare's side.
==================== ========== ===========

persistent
^^^^^^^^^^

=================== =========== ===========
Parameter           Type        Explanation
=================== =========== ===========
mode                ``string``  What mode this persistent onion uses. Options are "share", "receive", "website" or "chat".
enabled             ``boolean`` Whether persistence is enabled for this onion. When the persistent option is unchecked in the desktop, this entire JSON file is deleted. Default: true
autostart_on_launch ``boolean`` Whether to automatically start this persistent onion when OnionShare starts and once Tor is connected. Default: false
=================== =========== ===========

general
^^^^^^^

=============== =========== ===========
Parameter       Type        Explanation
=============== =========== ===========
title           ``string``  An optional custom title for displaying on the onion service. Default: null ("OnionShare" will be shown instead)
public          ``boolean`` Whether the onion service can be accessed with or without a Private Key (Client Authentication). If true, no Private Key is required.
autostart_timer ``boolean`` Whether the onion service is configured to start at a specific time. The time can be set in the desktop app or specified in seconds with ``--auto-start-timer`` with the CLI tool.
autostop_timer  ``boolean`` Whether the onion service is configured to stop at a specific time. The time can be set in the desktop app or specified in seconds with ``--auto-stop-timer`` with the CLI tool.
service_id      ``string``  The 32-character onion service URL, without the scheme and without the '.onion' suffix.
=============== =========== ===========

The below are settings specific to the 'mode' specified in the ``persistent`` section above.

share
^^^^^

================ =========== ===========
Parameter        Type        Explanation
================ =========== ===========
autostop_sharing ``boolean`` Whether to automatically stop the share once files are downloaded the first time. Default: true
filenames        ``list``    A list of files to share. Default: []
log_filenames    ``boolean`` Whether to log URL requests to stdout when using the CLI tool. Default: false
================ =========== ===========

receive
^^^^^^^

============= =========== ===========
Parameter     Type        Explanation
============= =========== ===========
data_dir      ``string``  The path where received files or text messages will be stored. Default: the 'OnionShare' folder of the user's home directory.
webhook_url   ``string``  A webhook URL that OnionShare will POST to when it receives files or text messages. Default: null
disable_text  ``boolean`` Whether to disable receiving text messages. Default: false
disable_files ``boolean`` Whether to disable receiving files. Default: false
============= =========== ===========

website
^^^^^^^

============= =========== ===========
Parameter     Type        Explanation
============= =========== ===========
disable_csp   ``boolean`` If set to ``true``, OnionShare won't set its default Content Security Policy header for the website. Default: ``false``
custom_csp    ``string``  A custom Content Security Policy header to send instead of the default.
log_filenames ``boolean`` Whether to log URL requests to stdout when using the CLI tool. Default: false
filenames     ``list``    A list of files to share. Default: []
============= =========== ===========

chat
^^^^

There are currently no configurable settings for the Chat mode.
