Developing OnionShare
=====================

.. _collaborating:

Collaborating
-------------

OnionShare has an open Keybase team to discuss the project, ask questions, share ideas and designs, and making plans for future development. (It's also an easy way to send end-to-end encrypted direct messages to others in the OnionShare community, like OnionShare addresses.)
To use Keybase, download the `Keybase app <https://keybase.io/download>`_, make an account, and `join this team <https://keybase.io/team/onionshare>`_. Within the app, go to "Teams", click "Join a Team", and type "onionshare".

OnionShare also has a `mailing list <https://lists.riseup.net/www/subscribe/onionshare-dev>`_ for developers and and designers to discuss the project.

Contributing Code
-----------------

OnionShare source code is to be found in this Git repository: https://github.com/onionshare/onionshare

If you'd like to contribute code to OnionShare, it helps to join the Keybase team and ask questions about what you're thinking of working on.
You should also review all of the `open issues <https://github.com/onionshare/onionshare/issues>`_ on GitHub to see if there are any you'd like to tackle.

When you're ready to contribute code, open a pull request in the GitHub repository and one of the project maintainers will review it and possibly ask questions, request changes, reject it, or merge it into the project.

.. _starting_development:

Starting Development
--------------------

OnionShare is developed in Python.
To get started, clone the Git repository at https://github.com/onionshare/onionshare/ and then consult the ``cli/README.md`` file to learn how to set up your development environment for the command-line version, and the ``desktop/README.md`` file to learn how to set up your development environment for the graphical version.

Those files contain the necessary technical instructions and commands install dependencies for your platform, and to run OnionShare from the source tree.

Debugging tips
--------------

Verbose mode
^^^^^^^^^^^^

When developing, it's convenient to run OnionShare from a terminal and add the ``--verbose`` (or ``-v``) flag to the command.
This prints a lot of helpful messages to the terminal, such as when certain objects are initialized, when events occur (like buttons clicked, settings saved or reloaded), and other debug info. For example::

    $ poetry run onionshare-cli -v ~/Documents/roms/nes/Q-bert\ \(USA\).nes 
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
    │                  v2.3.3                   │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯
    
    [Aug 28 2021 10:32:39] Settings.__init__
    [Aug 28 2021 10:32:39] Settings.load
    [Aug 28 2021 10:32:39] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=wordlist.txt
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=wordlist.txt, path=/home/user/git/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [Aug 28 2021 10:32:39] ModeSettings.load: creating /home/user/.config/onionshare/persistent/dreamy-stiffen-moving.json
    [Aug 28 2021 10:32:39] ModeSettings.set: updating dreamy-stiffen-moving: general.title = None
    [Aug 28 2021 10:32:39] ModeSettings.set: updating dreamy-stiffen-moving: general.public = False
    [Aug 28 2021 10:32:39] ModeSettings.set: updating dreamy-stiffen-moving: general.autostart_timer = 0
    [Aug 28 2021 10:32:39] ModeSettings.set: updating dreamy-stiffen-moving: general.autostop_timer = 0
    [Aug 28 2021 10:32:39] ModeSettings.set: updating dreamy-stiffen-moving: share.autostop_sharing = True
    [Aug 28 2021 10:32:39] Web.__init__: is_gui=False, mode=share
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=static
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=static, path=/home/user/git/onionshare/cli/onionshare_cli/resources/static
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=templates
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=templates, path=/home/user/git/onionshare/cli/onionshare_cli/resources/templates
    [Aug 28 2021 10:32:39] Web.generate_static_url_path: new static_url_path is /static_3tix3w3s5feuzlhii3zwqb2gpq
    [Aug 28 2021 10:32:39] ShareModeWeb.init
    [Aug 28 2021 10:32:39] Onion.__init__
    [Aug 28 2021 10:32:39] Onion.connect
    [Aug 28 2021 10:32:39] Settings.__init__
    [Aug 28 2021 10:32:39] Settings.load
    [Aug 28 2021 10:32:39] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 28 2021 10:32:39] Onion.connect: tor_data_directory_name=/home/user/.config/onionshare/tmp/tmppb7kvf4k
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=torrc_template
    [Aug 28 2021 10:32:39] Common.get_resource_path: filename=torrc_template, path=/home/user/git/onionshare/cli/onionshare_cli/resources/torrc_template
    Connecting to the Tor network: 100% - Done
    [Aug 28 2021 10:32:56] Onion.connect: Connected to tor 0.4.6.7
    [Aug 28 2021 10:32:56] Settings.load
    [Aug 28 2021 10:32:56] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 28 2021 10:32:56] OnionShare.__init__
    [Aug 28 2021 10:32:56] OnionShare.start_onion_service
    [Aug 28 2021 10:32:56] Onion.start_onion_service: port=17609
    [Aug 28 2021 10:32:56] Onion.start_onion_service: key_type=NEW, key_content=ED25519-V3
    [Aug 28 2021 10:33:03] ModeSettings.set: updating dreamy-stiffen-moving: general.service_id = sobp4rklarkz34mcog3pqtkb4t5bvyxv3dazvsqmfyhw4imqj446ffqd
    [Aug 28 2021 10:33:03] ModeSettings.set: updating dreamy-stiffen-moving: onion.private_key = sFiznwaPWJdKmFXumdDLkJGdUUdjI/0TWo+l/QEZiE/XoVogjK9INNoz2Tf8vmpe66ssa85En+5w6F2kKyTstA==
    [Aug 28 2021 10:33:03] ModeSettings.set: updating dreamy-stiffen-moving: onion.client_auth_priv_key = YL6YIEMZS6J537Y5ZKEA2Z6IIQEWFK2CMGTWK5G3DGGUREHJSJNQ
    [Aug 28 2021 10:33:03] ModeSettings.set: updating dreamy-stiffen-moving: onion.client_auth_pub_key = 5HUL6RCPQ5VEFDOHCSRAHPFIB74EHVFJO6JJHDP76EDWVRJE2RJQ
    Compressing files.
    [Aug 28 2021 10:33:03] ShareModeWeb.init
    [Aug 28 2021 10:33:03] ShareModeWeb.set_file_info_custom
    [Aug 28 2021 10:33:03] ShareModeWeb.build_zipfile_list
    [Aug 28 2021 10:33:03] Web.start: port=17609
     * Running on http://127.0.0.1:17609/ (Press CTRL+C to quit)
    
    Give this address and private key to the recipient:
    http://sobp4rklarkz34mcog3pqtkb4t5bvyxv3dazvsqmfyhw4imqj446ffqd.onion
    Private key: YL6YIEMZS6J537Y5ZKEA2Z6IIQEWFK2CMGTWK5G3DGGUREHJSJNQ
    
    Press Ctrl+C to stop the server


You can add your own debug messages by running the ``Common.log`` method from ``onionshare/common.py``. For example::

    common.log('OnionShareGui', 'start_server', 'I ran here')

This can be useful when learning the chain of events that occur when using OnionShare, or the value of certain variables before and after they are manipulated.

Local Only
^^^^^^^^^^

Tor is slow, and it's often convenient to skip starting onion services altogether during development.
You can do this with the ``--local-only`` flag. For example::

    $ poetry run onionshare-cli --local-only --receive
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
    │                  v2.3.3                   │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯
    
     * Running on http://127.0.0.1:17621/ (Press CTRL+C to quit)
    
    Files sent to you appear in this folder: /home/user/OnionShare
    
    Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing.
    
    Give this address and private key to the sender:
    http://127.0.0.1:17621
    Private key: E2GOT5LTUTP3OAMRCRXO4GSH6VKJEUOXZQUC336SRKAHTTT5OVSA
    
    Press Ctrl+C to stop the server

In this case, you load the URL ``http://127.0.0.1:17621`` in a normal web-browser like Firefox, instead of using the Tor Browser. The Private key is not actually needed in local-only mode, so you can ignore it.

Contributing Translations
-------------------------

Help make OnionShare easier to use and more familiar and welcoming for people by translating it on `Hosted Weblate <https://hosted.weblate.org/projects/onionshare/>`_. Always keep the "OnionShare" in latin letters, and use "OnionShare (localname)" if needed.

To help translate, make a Hosted Weblate account and start contributing.

Suggestions for Original English Strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes the original English strings are wrong, or don't match between the application and the documentation.

File source string improvements by adding @kingu to your Weblate comment, or open a GitHub issue or pull request.
The latter ensures all upstream developers see the suggestion, and can potentially modify the string via the usual code review processes.

Status of Translations
^^^^^^^^^^^^^^^^^^^^^^
Here is the current translation status.
If you want start a translation in a language not yet started, please write to the mailing list: onionshare-dev@lists.riseup.net

.. image:: https://hosted.weblate.org/widgets/onionshare/-/translations/multi-auto.svg
