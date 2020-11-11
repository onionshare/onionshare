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

    [Nov 10 2020 20:50:35] Settings.__init__
    [Nov 10 2020 20:50:35] Settings.load
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=wordlist.txt
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=wordlist.txt, path=/home/user/code/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [Nov 10 2020 20:50:35] ModeSettings.load: creating /home/user/.config/onionshare/persistent/abstain-reprogram-elevate.json
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: general.public = False
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: general.autostart_timer = 0
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: general.autostop_timer = 0
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: general.legacy = False
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: general.client_auth = False
    [Nov 10 2020 20:50:35] ModeSettings.set: updating abstain-reprogram-elevate: share.autostop_sharing = True
    [Nov 10 2020 20:50:35] Web.__init__: is_gui=False, mode=share
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=static
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=static, path=/home/user/code/onionshare/cli/onionshare_cli/resources/static
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=templates
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=templates, path=/home/user/code/onionshare/cli/onionshare_cli/resources/templates
    [Nov 10 2020 20:50:35] Web.generate_static_url_path: new static_url_path is /static_qa7rlyxwnfodczrriv3tj5yeoq
    [Nov 10 2020 20:50:35] ShareModeWeb.init
    [Nov 10 2020 20:50:35] Onion.__init__
    [Nov 10 2020 20:50:35] Onion.connect
    [Nov 10 2020 20:50:35] Settings.__init__
    [Nov 10 2020 20:50:35] Settings.load
    [Nov 10 2020 20:50:35] Onion.connect: tor_data_directory_name=/home/user/.config/onionshare/tmp/tmpz53ztq3m
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=torrc_template
    [Nov 10 2020 20:50:35] Common.get_resource_path: filename=torrc_template, path=/home/user/code/onionshare/cli/onionshare_cli/resources/torrc_template
    Connecting to the Tor network: 100% - Done
    [Nov 10 2020 20:50:42] Onion.connect: Connected to tor 0.4.4.5
    [Nov 10 2020 20:50:42] Settings.load
    [Nov 10 2020 20:50:42] Web.generate_password: saved_password=None
    [Nov 10 2020 20:50:42] Common.get_resource_path: filename=wordlist.txt
    [Nov 10 2020 20:50:42] Common.get_resource_path: filename=wordlist.txt, path=/home/user/code/onionshare/cli/onionshare_cli/resources/wordlist.txt
    [Nov 10 2020 20:50:42] Web.generate_password: built random password: "pedometer-grower"
    [Nov 10 2020 20:50:42] OnionShare.__init__
    [Nov 10 2020 20:50:42] OnionShare.start_onion_service
    [Nov 10 2020 20:50:42] Onion.start_onion_service: port=17610
    [Nov 10 2020 20:50:42] Onion.start_onion_service: key_type=NEW, key_content=ED25519-V3
    [Nov 10 2020 20:50:46] ModeSettings.set: updating abstain-reprogram-elevate: general.service_id = x5duatuhpiwfzb23iwpjanalvtxdhoj43ria44s53ryy5diywvbu24ad
    [Nov 10 2020 20:50:46] ModeSettings.set: updating abstain-reprogram-elevate: onion.private_key = uIXJzY+88tGSAXAjQxdwkzb2L7jHv467RIX1WDieVkFEZjEA7st2p/6uVCM4KM3L9PdShTPScuUv2IEbVQammA==
    Compressing files.
    [Nov 10 2020 20:50:46] ShareModeWeb.init
    [Nov 10 2020 20:50:46] ShareModeWeb.set_file_info_custom
    [Nov 10 2020 20:50:46] ShareModeWeb.build_zipfile_list
    [Nov 10 2020 20:50:46] Web.start: port=17610
    * Running on http://127.0.0.1:17610/ (Press CTRL+C to quit)

    Give this address to the recipient:
    http://onionshare:pedometer-grower@x5duatuhpiwfzb23iwpjanalvtxdhoj43ria44s53ryy5diywvbu24ad.onion

    Press Ctrl+C to stop the server

You can add your own debug messages by running the ``Common.log`` method from ``onionshare/common.py``. For example::

    common.log('OnionShareGui', 'start_server', 'I ran here')

This can be useful when learning the chain of events that occur when using OnionShare, or the value of certain variables before and after they are manipulated.

Local Only
^^^^^^^^^^

Tor is slow, and it's often convenient to skip starting onion services altogether during development.
You can do this with the ``--local-only`` flag. For example::

    $ poetry run onionshare-cli --local-only --receive
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

    * Running on http://127.0.0.1:17635/ (Press CTRL+C to quit)

    Files sent to you appear in this folder: /home/user/OnionShare

    Warning: Receive mode lets people upload files to your computer. Some files can potentially take control of your computer if you open them. Only open things from people you trust, or if you know what you are doing.

    Give this address to the sender:
    http://onionshare:train-system@127.0.0.1:17635

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