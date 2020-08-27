Developing OnionShare
=====================

.. _collaborating:

Collaborating
-------------

OnionShare has an open Keybase team that we use to discuss the project, including asking questions, sharing ideas and designs, and making plans for future development. (It's also an easy way to send end-to-end encrypted direct messages to others in the OnionShare community, like OnionShare addresses.) To use Keybase, you need to download the `Keybase app <https://keybase.io/download>`_, make an account, and `join this team <https://keybase.io/team/onionshare>`_. Within the app, go to Teams, click "Join a Team", and type "onionshare".

OnionShare also has a `mailing list <https://lists.riseup.net/www/subscribe/onionshare-dev>`_ for developers and and designers to discuss the project.

Contributing code
-----------------

OnionShare source code is in this git repository: https://github.com/micahflee/onionshare

If you'd like to contribute code to OnionShare, it helps to join the Keybase team and ask questions about what you're thinking of working on. You should also review all of the `open issues <https://github.com/micahflee/onionshare/issues>`_ on GitHub to see if there are any that you'd like to develop.

When you're ready to contribute code, open a pull request in the GitHub repository and one of the project maintainers will review it and possible ask questions, request changes, reject it, or merge it into the project.

Starting development
--------------------

OnionShare is developed in Python. To get started, you should close the git repository at https://github.com/micahflee/onionshare/ and then consult the ``BUILD.md`` file.

That file contains the technical instructions and commands necessary:

* Install dependencies for your platform
* Run OnionShare from the source tree, without building a package
* Building packages
* Making a release of OnionShare

Debugging tips
--------------

Verbose mode
^^^^^^^^^^^^

When developing, it's convenient to run OnionShare from a terminal and add the ``--verbose`` (or ``-v``) flag to the command. This will print a lot of helpful messages to the terminal such as when certain objects are initialized, when events occur (like buttons clicked, settings saved or reloaded), and other debug information. For example::

    $ poetry run ./dev_scripts/onionshare -v test.txt 
    OnionShare 2.3 | https://onionshare.org/

                        @@@@@@@@@                      
                    @@@@@@@@@@@@@@@@@@@                 
                @@@@@@@@@@@@@@@@@@@@@@@@@              
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
                @@@@@@@@@@@@@@@@@@@@@@@@@@@@@           ___        _               
                @@@@@@         @@@@@@@@@@@@@         / _ \      (_)              
            @@@@    @               @@@@@@@@@@@       | | | |_ __  _  ___  _ __    
        @@@@@@@@                   @@@@@@@@@@       | | | | '_ \| |/ _ \| '_ \   
        @@@@@@@@@@@@                  @@@@@@@@@@      \ \_/ / | | | | (_) | | | |  
    @@@@@@@@@@@@@@@@                 @@@@@@@@@       \___/|_| |_|_|\___/|_| |_|  
        @@@@@@@@@                 @@@@@@@@@@@@@@@@    _____ _                     
        @@@@@@@@@@                  @@@@@@@@@@@@     /  ___| |                    
        @@@@@@@@@@                   @@@@@@@@       \ `--.| |__   __ _ _ __ ___ 
        @@@@@@@@@@@               @    @@@@          `--. \ '_ \ / _` | '__/ _ \
            @@@@@@@@@@@@@         @@@@@@               /\__/ / | | | (_| | | |  __/
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@             \____/|_| |_|\__,_|_|  \___|
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
                @@@@@@@@@@@@@@@@@@@@@@@@@              
                    @@@@@@@@@@@@@@@@@@@                 
                        @@@@@@@@@                      

    [Aug 23 2020 22:37:06] Settings.__init__
    [Aug 23 2020 22:37:06] Settings.load
    [Aug 23 2020 22:37:06] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 23 2020 22:37:06] ModeSettings.load: creating /home/user/.config/onionshare/persistent/opacity-joining-sappiness.json
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: general.public = False
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: general.autostart_timer = 0
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: general.autostop_timer = 0
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: general.legacy = False
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: general.client_auth = False
    [Aug 23 2020 22:37:06] ModeSettings.set: updating opacity-joining-sappiness: share.autostop_sharing = True
    [Aug 23 2020 22:37:06] Web.__init__: is_gui=False, mode=share
    [Aug 23 2020 22:37:06] Web.generate_static_url_path: new static_url_path is /static_4kanwd4mt5mcqmpsbptviv3tbq
    [Aug 23 2020 22:37:06] ShareModeWeb.init
    [Aug 23 2020 22:37:06] Onion.__init__
    [Aug 23 2020 22:37:06] Onion.connect
    [Aug 23 2020 22:37:06] Settings.__init__
    [Aug 23 2020 22:37:06] Settings.load
    [Aug 23 2020 22:37:06] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 23 2020 22:37:06] Onion.connect: tor_data_directory_name=/home/user/.config/onionshare/tmp/tmpig895mfl
    Connecting to the Tor network: 14% - Handshaking with a relay
    Connecting to the Tor network: 25% - Asking for networkstatus consensus
    Connecting to the Tor network: 30% - Loading networkstatus consensus
    Connecting to the Tor network: 40% - Loading authority key certs
    Connecting to the Tor network: 45% - Asking for relay descriptors
    Connecting to the Tor network: 50% - Loading relay descriptors
    Connecting to the Tor network: 59% - Loading relay descriptors
    Connecting to the Tor network: 68% - Loading relay descriptors
    Connecting to the Tor network: 89% - Finishing handshake with a relay to build circuits
    Connecting to the Tor network: 95% - Establishing a Tor circuit
    Connecting to the Tor network: 100% - Done

    [Aug 23 2020 22:37:14] Onion.connect: Connected to tor 0.4.3.6
    [Aug 23 2020 22:37:14] Settings.load
    [Aug 23 2020 22:37:14] Settings.load: Trying to load /home/user/.config/onionshare/onionshare.json
    [Aug 23 2020 22:37:14] Web.generate_password: saved_password=None
    [Aug 23 2020 22:37:14] Web.generate_password: built random password: "barrel-unseated"
    [Aug 23 2020 22:37:14] OnionShare.__init__
    [Aug 23 2020 22:37:14] OnionShare.start_onion_service
    [Aug 23 2020 22:37:14] Onion.start_onion_service: port=17605
    [Aug 23 2020 22:37:14] Onion.start_onion_service: key_type=NEW, key_content=ED25519-V3
    [Aug 23 2020 22:37:16] ModeSettings.set: updating opacity-joining-sappiness: general.service_id = ttxidvsv4pqzrarvtlojk435vver6wgifrw4pucyzgj2hb3qu6pf6fqd
    [Aug 23 2020 22:37:16] ModeSettings.set: updating opacity-joining-sappiness: onion.private_key = IGzO65Mi9grG7HlLD9ky82O/vWvu3WVByTqCLpZgV0iV2XaSDAqWazNHKkkP18/7jyZZyXwbLo4qOCiYLudlRA==
    Compressing files.
    [Aug 23 2020 22:37:16] ShareModeWeb.init
    [Aug 23 2020 22:37:16] ShareModeWeb.set_file_info_custom
    [Aug 23 2020 22:37:16] ShareModeWeb.build_zipfile_list
    [Aug 23 2020 22:37:16] Web.start: port=17605
    * Running on http://127.0.0.1:17605/ (Press CTRL+C to quit)

    Give this address to the recipient:
    http://onionshare:barrel-unseated@ttxidvsv4pqzrarvtlojk435vver6wgifrw4pucyzgj2hb3qu6pf6fqd.onion

    Press Ctrl+C to stop the server

You can add your own debug messages by running the ``Common.log`` method from ``onionshare/common.py``. For example::

    common.log('OnionShareGui', 'start_server', 'I ran here')

This can be useful when learning the chain of events that occur when using the application or the value of certain variables before and after they are manipulated.

Local only
^^^^^^^^^^

Tor is slow, and it's often convenient to skip starting onion services altogether during development. You can do this with the ``--local-only`` flag. For example::

    $ poetry run ./dev_scripts/onionshare --local-only --receive
    OnionShare 2.3 | https://onionshare.org/

                        @@@@@@@@@                      
                    @@@@@@@@@@@@@@@@@@@                 
                @@@@@@@@@@@@@@@@@@@@@@@@@              
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
                @@@@@@@@@@@@@@@@@@@@@@@@@@@@@           ___        _               
                @@@@@@         @@@@@@@@@@@@@         / _ \      (_)              
            @@@@    @               @@@@@@@@@@@       | | | |_ __  _  ___  _ __    
        @@@@@@@@                   @@@@@@@@@@       | | | | '_ \| |/ _ \| '_ \   
        @@@@@@@@@@@@                  @@@@@@@@@@      \ \_/ / | | | | (_) | | | |  
    @@@@@@@@@@@@@@@@                 @@@@@@@@@       \___/|_| |_|_|\___/|_| |_|  
        @@@@@@@@@                 @@@@@@@@@@@@@@@@    _____ _                     
        @@@@@@@@@@                  @@@@@@@@@@@@     /  ___| |                    
        @@@@@@@@@@                   @@@@@@@@       \ `--.| |__   __ _ _ __ ___ 
        @@@@@@@@@@@               @    @@@@          `--. \ '_ \ / _` | '__/ _ \
            @@@@@@@@@@@@@         @@@@@@               /\__/ / | | | (_| | | |  __/
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@             \____/|_| |_|\__,_|_|  \___|
            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
                @@@@@@@@@@@@@@@@@@@@@@@@@              
                    @@@@@@@@@@@@@@@@@@@                 
                        @@@@@@@@@                      

    * Running on http://127.0.0.1:17614/ (Press CTRL+C to quit)

    Files sent to you appear in this folder: /home/user/OnionShare

    Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing.

    Give this address to the sender:
    http://onionshare:eject-snack@127.0.0.1:17614

    Press Ctrl+C to stop the server

In this case, you load the URL ``http://onionshare:eject-snack@127.0.0.1:17614`` in a normal web browser like Firefox, instead of using Tor Browser.

Debugging in Windows
^^^^^^^^^^^^^^^^^^^^

If you want to obtain debug output from the ``onionshare-gui.exe`` in Windows, you will need to edit ``install\pyinstaller.spec`` and change ``console=False`` to ``console=True``.

Then rebuild the EXE with ``install\build_exe.bat`` (you may need to comment out the ``signtool`` commands in the ``build_exe.bat`` and the ``onionshare.nsi`` files, as per the ``BUILD.md`` instructions).

After this, you can run ``onionshare-gui.exe -v`` from a command prompt to see the debug output.

Contributing translations
-------------------------

Most of the OnionShare is translatable. You can help make it easier to use and more familiar and welcoming for people around the globe. The Localization Lab has some `documentation about translating OnionShare <https://wiki.localizationlab.org/index.php/OnionShare>`_.

OnionShare uses Weblate to keep track of translations. You can view the OnionShare project here: https://hosted.weblate.org/projects/onionshare/

To help translate, make a Hosted Weblate account and start contributing to that project.

Suggestions for original English strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes the original English strings could be improved, making them easier to translate into other languages.

If you have suggestions for a better English string, please open a GitHub issue rather than commenting in Weblate. This ensures the upstream developers will definitely see the suggestion, and can potentially modify the string via the usual code review processes.

Status of translations
^^^^^^^^^^^^^^^^^^^^^^
Here is the current translation status. If you want start a translation in a language not to be found here, please write us to the mailing list: onionshare-dev@lists.riseup.net

.. image:: https://hosted.weblate.org/widgets/onionshare/-/translations/multi-auto.svg

Translate the .desktop file
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also translate the ``install/onionshare.desktop`` file.

Duplicate the line that begins with ``Comment=``. Add the language code to the new line so it becomes ``Comment[lang]=`` (lang should be your language). You can see what language codes are used for translation by looking at the ``share/locale/*.json`` filenames::

    Comment=Original string
    Comment[da]=Danish translation of the original string

Do the same for other untranslated lines.