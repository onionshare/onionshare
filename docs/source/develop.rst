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

OnionShare source code is to be found in this Git repository: https://github.com/micahflee/onionshare

If you'd like to contribute code to OnionShare, it helps to join the Keybase team and ask questions about what you're thinking of working on.
You should also review all of the `open issues <https://github.com/micahflee/onionshare/issues>`_ on GitHub to see if there are any you'd like to tackle.

When you're ready to contribute code, open a pull request in the GitHub repository and one of the project maintainers will review it and possibly ask questions, request changes, reject it, or merge it into the project.

.. _starting_development:

Starting Development
--------------------

OnionShare is developed in Python.
To get started, clone the Git repository at https://github.com/micahflee/onionshare/ and then consult the ``cli/README.md`` file to learn how to set up your development environment for the command-line version, and the ``desktop/README.md`` file to learn how to set up your development environment for the graphical version.

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
    │                v2.3.2.dev1                 │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯
    
    [May 10 2021 18:24:02] Settings.__init__
    [May 10 2021 18:24:02] Settings.load
    [May 10 2021 18:24:02] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [May 10 2021 18:24:02] Common.get_resource_path: filename=wordlist.txt
    [May 10 2021 18:24:02] Common.get_resource_path: filename=wordlist.txt, path=/home/user/code/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [May 10 2021 18:24:02] ModeSettings.load: creating /home/user/.config/onionshare/persistent/tattered-handgun-stress.json
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.title = None
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.public = False
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.autostart_timer = 0
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.autostop_timer = 0
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.legacy = False
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: general.client_auth = False
    [May 10 2021 18:24:02] ModeSettings.set: updating tattered-handgun-stress: share.autostop_sharing = True
    [May 10 2021 18:24:02] Web.__init__: is_gui=False, mode=share
    [May 10 2021 18:24:02] Common.get_resource_path: filename=static
    [May 10 2021 18:24:02] Common.get_resource_path: filename=static, path=/home/user/code/onionshare/cli/onionshare_cli/resources/static
    [May 10 2021 18:24:02] Common.get_resource_path: filename=templates
    [May 10 2021 18:24:02] Common.get_resource_path: filename=templates, path=/home/user/code/onionshare/cli/onionshare_cli/resources/templates
    [May 10 2021 18:24:02] Web.generate_static_url_path: new static_url_path is /static_4yxrx2mzi5uzkblklpzd46mwke
    [May 10 2021 18:24:02] ShareModeWeb.init
    [May 10 2021 18:24:02] Onion.__init__
    [May 10 2021 18:24:02] Onion.connect
    [May 10 2021 18:24:02] Settings.__init__
    [May 10 2021 18:24:02] Settings.load
    [May 10 2021 18:24:02] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [May 10 2021 18:24:02] Onion.connect: tor_data_directory_name=/home/user/.config/onionshare/tmp/tmpw6u0nz8l
    [May 10 2021 18:24:02] Common.get_resource_path: filename=torrc_template
    [May 10 2021 18:24:02] Common.get_resource_path: filename=torrc_template, path=/home/user/code/onionshare/cli/onionshare_cli/resources/torrc_template
    Connecting to the Tor network: 100% - Done
    [May 10 2021 18:24:10] Onion.connect: Connected to tor 0.4.5.7
    [May 10 2021 18:24:10] Settings.load
    [May 10 2021 18:24:10] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [May 10 2021 18:24:10] Web.generate_password: saved_password=None
    [May 10 2021 18:24:10] Common.get_resource_path: filename=wordlist.txt
    [May 10 2021 18:24:10] Common.get_resource_path: filename=wordlist.txt, path=/home/user/code/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [May 10 2021 18:24:10] Web.generate_password: built random password: "tipping-colonize"
    [May 10 2021 18:24:10] OnionShare.__init__
    [May 10 2021 18:24:10] OnionShare.start_onion_service
    [May 10 2021 18:24:10] Onion.start_onion_service: port=17645
    [May 10 2021 18:24:10] Onion.start_onion_service: key_type=NEW, key_content=ED25519-V3
    [May 10 2021 18:24:14] ModeSettings.set: updating tattered-handgun-stress: general.service_id = omxjamkys6diqxov7lxru2upromdprxjuq3czdhen6hrshzd4sll2iyd
    [May 10 2021 18:24:14] ModeSettings.set: updating tattered-handgun-stress: onion.private_key = 6PhomJCjlWicmOyAAe0wnQoEM3vcyHBivrRGDy0hzm900fW5ITDJ6iv2+tluLoueYj81MhmnYeTOHDm8UGOfhg==
    Compressing files.
    [May 10 2021 18:24:14] ShareModeWeb.init
    [May 10 2021 18:24:14] ShareModeWeb.set_file_info_custom
    [May 10 2021 18:24:14] ShareModeWeb.build_zipfile_list
    [May 10 2021 18:24:14] Web.start: port=17645
    * Running on http://127.0.0.1:17645/ (Press CTRL+C to quit)
    
    Give this address to the recipient:
    http://onionshare:tipping-colonize@omxjamkys6diqxov7lxru2upromdprxjuq3czdhen6hrshzd4sll2iyd.onion
    
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
    │                v2.3.2.dev1                 │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯
    
    * Running on http://127.0.0.1:17617/ (Press CTRL+C to quit)
    
    Files sent to you appear in this folder: /home/user/OnionShare
    
    Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing.
    
    Give this address to the sender:
    http://onionshare:ended-blah@127.0.0.1:17617
    
    Press Ctrl+C to stop the server

In this case, you load the URL ``http://onionshare:train-system@127.0.0.1:17635`` in a normal web-browser like Firefox, instead of using the Tor Browser.

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