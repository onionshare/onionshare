How OnionShare Works
====================

OnionShare works by starting web servers locally on your own computer and making them accessible to other people as `Tor <https://www.torproject.org/>`_ `onion services <https://community.torproject.org/onion-services/>`_.

By default, OnionShare web addresses are protected with a random password. A typical OnionShare address might look something like this::

    http://onionshare:constrict-purity@by4im3ir5nsvygprmjq74xwplrkdgt44qmeapxawwikxacmr3dqzyjad.onion

In this case, the Tor onion address is ``by4im3ir5nsvygprmjq74xwplrkdgt44qmeapxawwikxacmr3dqzyjad.onion`` -- this is random, and each time you use OnionShare you'll get a different onion address. The username is always ``onionshare`` and the random password is ``constrict-purity``.

You're responsible for securely sharing that URL using a communication channel of their choice such as in an encrypted chat message, or using something less secure like a Twitter or Facebook message, depending on their `threat model <https://ssd.eff.org/en/module/your-security-plan>`_.

The people who you send the URL to must then copy and paste it into `Tor Browser <https://www.torproject.org/>`_ (a privacy-protecting anonymous web browser) to access the OnionShare service.

With OnionShare, *your own computer is the web server*. If you run OnionShare on your laptop to send someone files, and then suspends your laptop before the files have been downloaded, the service will not be available until your laptop is unsuspended and connected to the internet again. OnionShare works best when working with people in real-time.

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
