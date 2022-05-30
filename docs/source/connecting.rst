Getting connected to Tor
========================

When OnionShare starts, it will show you a screen asking you to connect to the Tor network.

.. image:: _static/screenshots/autoconnect-welcome-screen.png

You can click "Connect to Tor" to begin the connection process. If there are no problems with your network, including any attempts to block your access to the Tor network, this should hopefully work the first time.

Or, if you want to manually configure Bridges or other Tor settings before you connect, you can click "Network Settings".

Automatic censorship circumvention
----------------------------------

When OnionShare fails to connect to Tor, it might be because Tor is censored in your country or on your local network.

If this occurs, you will have these choices:

- Try again without a bridge
- Automatically determine my country from my IP address for bridge settings
- Manually select my country for bridge settings

.. image:: _static/screenshots/autoconnect-failed-to-connect.png

Here's what each option does.

Try again without a bridge
^^^^^^^^^^^^^^^^^^^^^^^^^^

This will retry the normal OnionShare connection attempt to Tor without attempting to bypass censorship.

Automatically determine my country from my IP address for bridge settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This will attempt to automatically bypass censorship. It works by using Tor bridges.
If your network provider is blocking access to the Tor network, you can hopefully still connect to a Tor bridge, which will then connect you to the Tor network.

This option uses the Tor Project's Censorship Circumvention API to determine your country and, based on that, provide you with bridge settings that should work for you.
OnionShare will temporarily use the `Meek <https://gitlab.torproject.org/legacy/trac/-/wikis/doc/meek/>`_ domain-fronting proxy to make a non-Tor connection from your computer to Tor's Censorship Circumvention API. The Meek proxy hides the fact that you are trying to find a way to connect to Tor.
The Censorship Circumvention API will consider your IP address (yes, your real IP address) to determine what country you might reside in.
Based on the country information, the API will try to automatically find bridges that suit your location.

.. image:: _static/screenshots/autoconnect-trying-to-resolve-connectivity-issues.png

(add another screenshot of it connecting more successfully)

Manually select my country for bridge settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just live the previous option, this will attempt to bypass censorship using Tor Project's Censorship API. But rather than the API determining your country from your IP address, it will fetch bridges for the country that you specified.

If it finds any such bridges, OnionShare will try to reconnect to Tor using those bridges.

If the API does not find any bridges for your location, OnionShare will ask the API for "fallback" options. At the time of writing, this is likely to be the obfs4 built-in bridges.

OnionShare will also attempt to use the obfs4 built-in bridges if for some reason it could not connect to the API itself, or the API returned an error.

It's important to note that the requests to the Censorship Circumvention API do not go over the Tor Network (because if you could connect to Tor already, you wouldn't need to connect to the API).

Even though it is hard for an adversary to discover where the Meek request is going, this may still be risky for some users. Therefore, it is an opt-in feature. The use of Meek and non-torified network requests are limited only to making one or two requests to the Censorship Circumvention API. Then Meek is stopped, and all further network requests happen over the Tor network.

If you are uncomfortable with making a request that doesn't go over the Tor network, you can click the Network Settings (or the Settings icon in the bottom right corner, followed by the Tor Settings tab in the screen that appears), and manually configure bridges. After you save any bridge settings, OnionShare will try to reconnect using those bridges.

Connect to Tor automatically
----------------------------

You can toggle on the switch "Connect to Tor automatically" before clicking "Connect to Tor". This means that next time OnionShare starts, it will automatically connect with its Tor connection settings from the last session, instead of presenting you with the connection options.

If the connection fails, you can still try bridges or reconfigure Tor via the "Network Settings" button.
