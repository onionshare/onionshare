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
    │                  v2.4.1                   │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯

    [Sep 09 2021 19:13:20] Settings.__init__
    [Sep 09 2021 19:13:20] Settings.load
    [Sep 09 2021 19:13:20] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=wordlist.txt
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=wordlist.txt, path=/home/user/code/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [Sep 09 2021 19:13:20] ModeSettings.load: creating /home/user/.config/onionshare/persistent/polish-pushpin-hydrated.json
    [Sep 09 2021 19:13:20] ModeSettings.set: updating polish-pushpin-hydrated: general.title = None
    [Sep 09 2021 19:13:20] ModeSettings.set: updating polish-pushpin-hydrated: general.public = False
    [Sep 09 2021 19:13:20] ModeSettings.set: updating polish-pushpin-hydrated: general.autostart_timer = 0
    [Sep 09 2021 19:13:20] ModeSettings.set: updating polish-pushpin-hydrated: general.autostop_timer = 0
    [Sep 09 2021 19:13:20] ModeSettings.set: updating polish-pushpin-hydrated: share.autostop_sharing = True
    [Sep 09 2021 19:13:20] Web.__init__: is_gui=False, mode=share
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=static
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=static, path=/home/user/code/onionshare/cli/onionshare_cli/resources/static
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=templates
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=templates, path=/home/user/code/onionshare/cli/onionshare_cli/resources/templates
    [Sep 09 2021 19:13:20] Web.generate_static_url_path: new static_url_path is /static_gvvq2hplxhs2cekk665kagei6m
    [Sep 09 2021 19:13:20] ShareModeWeb.init
    [Sep 09 2021 19:13:20] Onion.__init__
    [Sep 09 2021 19:13:20] Onion.connect
    [Sep 09 2021 19:13:20] Settings.__init__
    [Sep 09 2021 19:13:20] Settings.load
    [Sep 09 2021 19:13:20] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Sep 09 2021 19:13:20] Onion.connect: tor_data_directory_name=/home/user/.config/onionshare/tmp/tmpf3akiouy
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=torrc_template
    [Sep 09 2021 19:13:20] Common.get_resource_path: filename=torrc_template, path=/home/user/code/onionshare/cli/onionshare_cli/resources/torrc_template
    Connecting to the Tor network: 100% - Done
    [Sep 09 2021 19:13:30] Onion.connect: Connected to tor 0.4.6.7
    [Sep 09 2021 19:13:30] Settings.load
    [Sep 09 2021 19:13:30] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Sep 09 2021 19:13:30] OnionShare.__init__
    [Sep 09 2021 19:13:30] OnionShare.start_onion_service
    [Sep 09 2021 19:13:30] Onion.start_onion_service: port=17616
    [Sep 09 2021 19:13:30] Onion.start_onion_service: key_type=NEW, key_content=ED25519-V3
    [Sep 09 2021 19:13:35] ModeSettings.set: updating polish-pushpin-hydrated: general.service_id = vucwsdmjt7szoc6pel3puqoxobiepdsowmqaq7pm7dzhembtzr2capad
    [Sep 09 2021 19:13:35] ModeSettings.set: updating polish-pushpin-hydrated: onion.private_key = +HfFALM4MtrNh59ibfMtRwDCIpfpWHIcNh3boahqrHh3TkLAyQvzKTm/y53KoYKSh0VU+m9DZY7DtZuCzkHkqQ==
    [Sep 09 2021 19:13:35] ModeSettings.set: updating polish-pushpin-hydrated: onion.client_auth_priv_key = G24TSNLIJX7YZM6R7P24AIGRU4N56ZFL7ENZVIDIWUEWY66YS3EQ
    [Sep 09 2021 19:13:35] ModeSettings.set: updating polish-pushpin-hydrated: onion.client_auth_pub_key = GDY2EPXSS7Q3ELQJFIX2VELTVZ3QEYIGWIZ26CEDQKZJ5Y7VKI3A
    Compressing files.
    [Sep 09 2021 19:13:35] ShareModeWeb.init
    [Sep 09 2021 19:13:35] ShareModeWeb.set_file_info_custom
    [Sep 09 2021 19:13:35] ShareModeWeb.build_zipfile_list
    [Sep 09 2021 19:13:35] Web.start: port=17616
    * Running on http://127.0.0.1:17616/ (Press CTRL+C to quit)

    Give this address and private key to the recipient:
    http://vucwsdmjt7szoc6pel3puqoxobiepdsowmqaq7pm7dzhembtzr2capad.onion
    Private key: G24TSNLIJX7YZM6R7P24AIGRU4N56ZFL7ENZVIDIWUEWY66YS3EQ

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
    │                  v2.4.1                   │
    │                                           │
    │          https://onionshare.org/          │
    ╰───────────────────────────────────────────╯

    * Running on http://127.0.0.1:17641/ (Press CTRL+C to quit)

    Files sent to you appear in this folder: /home/user/OnionShare

    Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing.

    Give this address and private key to the sender:
    http://127.0.0.1:17641
    Private key: E2GOT5LTUTP3OAMRCRXO4GSH6VKJEUOXZQUC336SRKAHTTT5OVSA

    Press Ctrl+C to stop the server


In this case, you load the URL ``http://127.0.0.1:17641`` in a normal web-browser like Firefox, instead of using the Tor Browser. The private key is not actually needed in local-only mode, so you can ignore it.

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
