How it Works
============

OnionShare works by starting web servers locally on your own computer (at ``127.0.0.1`` on a random port between 17600 and 17650), and then making them accessible to other people as a `Tor <https://www.torproject.org/>`_ `onion service <https://community.torproject.org/onion-services/>`_.

By default, OnionShare web addresses are password protected. The username is always ``onionshare`` and the password is randomly generated. For example, a typical OnionShare address might look something like this::

    http://onionshare:constrict-purity@by4im3ir5nsvygprmjq74xwplrkdgt44qmeapxawwikxacmr3dqzyjad.onion

In this case, the Tor onion address is ``by4im3ir5nsvygprmjq74xwplrkdgt44qmeapxawwikxacmr3dqzyjad.onion`` -- this is random, and each time you use OnionShare you'll get a different onion address. The username is ``onionshare`` and the random password is ``constrict-purity``.

The OnionShare user is responsible for securely sharing that URL with their audience using a communication channel of their choice such as in an encrypted chat message, or something less secure like a Twitter or Facebook message, depending on their threat model.

The members of the audience must use `Tor Browser <https://www.torproject.org/>`_ to load the URL and access the OnionShare service.

With OnionShare, *your own computer is the web server*. If you start an OnionShare service and send the URL to someone, you must keep your computer turned on and connected to the internet or else the service will go down. Because of this, OnionShare is most useful if it's used in real-time.

For example, if a user runs OnionShare on their laptop to send someone files, and then suspends their laptop before the files have been downloaded, the service will not be available until the laptop is unsuspended and connected to the internet again.

Because your own computer is the web server, *no third party can access anything that happens in OnionShare*, not even the developers of OnionShare. It's completely private. And because OnionShare is based on Tor onion services too, it also protects your anonymity. See the :doc:`security design </security>` for more information.

Connecting to Tor
-----------------

Share Files
-----------

You can use OnionShare to securely and anonymously send files and folders to people. Just open OnionShare, drag in the files and folders you wish to share, and click "Start sharing".

Receive Files
-------------

Host a Website
--------------

Chat Anonymously
----------------
