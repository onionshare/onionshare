How OnionShare Works
====================

OnionShare works by starting web servers locally on your own computer and making them accessible to other people as `Tor <https://www.torproject.org/>`_ `onion services <https://community.torproject.org/onion-services/>`_.

By default, OnionShare web addresses are protected with a random password. A typical OnionShare address might look something like this::

    http://onionshare:constrict-purity@by4im3ir5nsvygprmjq74xwplrkdgt44qmeapxawwikxacmr3dqzyjad.onion

You're responsible for securely sharing that URL using a communication channel of your choice like in an encrypted chat message, or using something less secure like a Twitter or Facebook message, depending on your `threat model <https://ssd.eff.org/en/module/your-security-plan>`_.

The people who you send the URL to must then copy and paste it into `Tor Browser <https://www.torproject.org/>`_ to access the OnionShare service.

With OnionShare, *your own computer is the web server*. If you run OnionShare on your laptop to send someone files, and then suspends your laptop before the files have been downloaded, the service will not be available until your laptop is unsuspended and connected to the internet again. OnionShare works best when working with people in real-time.

Because your own computer is the web server, *no third party can access anything that happens in OnionShare*, not even the developers of OnionShare. It's completely private. And because OnionShare is based on Tor onion services too, it also protects your anonymity. See the :doc:`security design </security>` for more information.

Share Files
-----------

You can use OnionShare to securely and anonymously send files and folders to people. Just open a share tab, drag in the files and folders you wish to share, and click "Start sharing".

.. image:: _static/screenshots/share.png

After you add files, you'll see some settings. Make sure you choose the setting you're interested in first before you start sharing.

.. image:: _static/screenshots/share-files.png

By default, as soon as someone finishes downloading your files, OnionShare will automatically stop the server, completely removing the website from the internet. If you want to allow multiple people to download these files, uncheck the "Stop sharing after files have been sent (uncheck to allow downloading individual files)" box.

Also, if you uncheck this box, people will be able to download individual files that you share rather than a single compressed version of all of the files.

When you're ready to share, click the "Start sharing" button. You can always click "Stop sharing", or quit OnionShare, to immediate take the website down. You can also click the up arrow icon in the top-right corner to show the history and progress of people downloading files from you.

.. image:: _static/screenshots/share-sharing.png

Now that you have a website that's sharing files, copy the address and send it to the person you want to receive the files. If the files need to stay secure, you should use an encrypted messaging app.

That person then must load the address in Tor Browser. After logging in with the random password that's included in the web address, they will be able to download the files directly from your computer by clicking the "Download Files" link in the corner.

.. image:: _static/screenshots/share-torbrowser.png

Receive Files
-------------

You can use OnionShare to let people anonymously upload files directly to your computer, essentially turning it into an anonymous dropbox. Open a receive tab, choose where you want files to get downloaded and other settings, and then click "Start Receive Mode".

.. image:: _static/screenshots/receive.png

This will start the OnionShare service. Anyone that loads this address in Tor Browser will be able to upload files to your computer.

.. image:: _static/screenshots/receive-sharing.png

You can also click the down arrow icon in the top-right corner to show the history and progress of people sending files to you.

Here is what it looks like for someone sending you files.

.. image:: _static/screenshots/receive-torbrowser.png

When someone uploads files to your receive service, by default they get saved to a folder called ``OnionShare`` in your home folder on your computer, and they get automatically organized into separate subfolders based on the time that the files get uploaded.

Setting up an OnionShare receiving service is useful for journalists and others that need to securely accept documents from anonymous sources. When used in this way, OnionShare is sort of like a lightweight, simpler, not quite as secure version of `SecureDrop <https://securedrop.org/>`_, the whistleblower submission system.

Use at your own risk
^^^^^^^^^^^^^^^^^^^^

Just like with malicious email attachments, it's possible that someone could try to hack your computer by uploading a malicious file to your OnionShare service. OnionShare does not add any safety mechanisms to protect your system from malicious files, so use at your own risk.

If you receive an Office document or a PDF through OnionShare, you can convert these documents into PDFs that you know are safe to open using `Dangerzone <https://dangerzone.rocks/>`_. You can also protect yourself when opening untrusted documents by opening them in `Tails <https://tails.boum.org/>`_ or in a `Qubes <https://qubes-os.org/>`_ disposable VM.

Tips for running a receive service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to host your own anonymous dropbox using OnionShare, it's recommended that you do it on a separate, dedicated computer that's always powered on and connected to the internet, and not on the one you use on a regular basis.

If you intend on advertising the OnionShare address on your website or social media profiles, then you should save the tab (see :ref:`save_tabs`) and run it as a public service (see :ref:`disable_passwords`).

Host a Website
--------------

You can use OnionShare to host a static HTML website with just a click. Just open a website tab, drag in the files and folders that make up the static website, and click when you're ready click "Start sharing".

.. image:: _static/screenshots/website.png

If you add an ``index.html`` file, when someone loads your website it will render this page. You should also include any other HTML files, CSS files, JavaScript files, and images that make up the website. (Note that OnionShare only supports hosting *static* websites. It can't host websites that execute code or use databases. So you can't, for example, use WordPress.)

If you don't have an ``index.html`` file, then it will show a directory listing instead, and people who load it can look through the files and download them.

After you add files, you'll see some settings. Make sure you choose the setting you're interested in first before you start sharing.

.. image:: _static/screenshots/website-files.png

Content Security Policy
^^^^^^^^^^^^^^^^^^^^^^^

By default OnionShare will help secure your website by setting a strict `Content Security Police <https://en.wikipedia.org/wiki/Content_Security_Policy>`_ header. However this will prevent third-party content from loading inside the web page.

If you want to load content from third-party websites, like assets or JavaScript libraries from CDNs, then you must check the "Disable Content Security Policy header (allows your website to use third-party resources)" box before starting the service.

Tips for running a website service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to host a long-term website using OnionShare (that isn't just to quickly show someone something), it's recommended that you do it on a separate, dedicated computer that's always powered on and connected to the internet, and not on the one you use on a regular basis. You should also save the tab (see :ref:`save_tabs`) so that you can resume the website with the same address if you close OnionShare and re-open it later.

If your website is intended to be viewed by the public, you should run it as a public service (see :ref:`disable_passwords`).

Chat Anonymously
----------------

You can use OnionShare to set up a completely anonymous, secure chat room that doesn't log anything or leave any traces. Just open a chat tab and click "Start chat server".

.. image:: _static/screenshots/chat.png

After you start the server, copy the OnionShare address and send it to the people who will join this anonymous chat room. If it's important to limit exactly who can join, you should use an encrypted messaging app to send the OnionShare address.

.. image:: _static/screenshots/chat-sharing.png

People can join the chat room by loading its OnionShare address in Tor Browser. The chat room requires JavasScript, so everyone who wants to participate must set their security level to Standard or Safer instead of Safest.

When someone joins the chat room they get assigned a random name which they can change in the left panel if they want. No chat history will get displayed at all, even if others were already chatting in the room, because the chat history isn't saved anywhere.

.. image:: _static/screenshots/chat-torbrowser.png

In an OnionShare chat room, everyone is anonymous. Anyone can change their name to anything, and there is no way to confirm anyone's identity.

However, if you create an OnionShare chat room and securely send the address only to a small group of trusted friends using encrypted messages, then you can be reasonably confident that the people who join the chat room are your friends.

How is this useful?
^^^^^^^^^^^^^^^^^^^

If you need to already be using an encrypted messaging app, what's the point of an OnionShare chat room to begin with? It leaves less traces.

If you send a message to a Signal group, for example, a copy of your message ends up on each device (the phones and computers, if they set up Signal Desktop) of each member of the group. Even if disappearing messages is enabled, it's hard to confirm that all copies of the messages were actually deleted from all devices, and from any other places (like notifications databases) they may have been saved to. OnionShare chat rooms don't store any messages anywhere, so this isn't a problem.

OnionShare chat rooms can also be useful for anonymous people wanting to chat securely with someone without needing to create any accounts. For example, a source can send an OnionShare address to a journalist using a disposable email address, and then wait for the journalist to join the chat room, all without compromosing their anonymity.

How does the encryption work?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because OnionShare relies on Tor onion services, connections between Tor Browser and OnionShare are all end-to-end encrypted (E2EE). When someone posts a message to an OnionShare chat room, they send it to the server through the E2EE onion connection, which then sends it to all other members of the chat room using WebSockets, through their E2EE onion connections.

OnionShare doesn't implement any chat encryption on its own. It relies on the Tor onion service's encryption instead.

Connecting to Tor
-----------------

There are several options for how OnionShare should connect to Tor. You can change them in Settings, which you can get to by clicking the gear icon in the bottom-right of the window.

.. image:: _static/screenshots/settings.png

Use Tor that is bundled with OnionShare
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the default way that OnionShare connects to Tor, and it's also the simplest and most reliable way. For this reason, it's recommended for most users.

When you open OnionShare, it will launch a Tor process in the background that's configured specifically for OnionShare to use. This Tor process won't interfere with other Tor processes on your computer, so you're free to run Tor Browser or use a system Tor in the background.

Attempt automatic configuration with Tor Browser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can configure OnionShare to connect to the Tor that comes with Tor Browser. First, `download Tor Browser <https://www.torproject.org>`_ here if you don't already have it. With this setting selected, you need to keep Tor Browser open in the background while you're using OnionShare.

Using a system Tor in Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is fairly advanced. You'll need to know how edit plaintext files and do stuff as an administrator.

Download the Tor Windows Expert Bundle, which you can get `from here <https://www.torproject.org/download/tor/>`_. Extract the zip file and copy the extracted folder to ``C:\Program Files (x86)\``, and rename the folder to ``tor-win32``, so that inside that folder is the ``Data`` and ``Tor`` folders.

Make up a control port password. I'm going to use ``comprised stumble rummage work avenging construct volatile`` as my password. Now open a command prompt as an administrator, and use ``tor.exe --hash-password`` to generate a hash of your password. For example::

    cd "C:\Program Files (x86)\tor-win32\Tor"
    tor.exe --hash-password "comprised stumble rummage work avenging construct volatile"

The hashed password output is displayed after some warnings (which you can ignore). In my case, it was ``16:00322E903D96DE986058BB9ABDA91E010D7A863768635AC38E213FDBEF``.

Now create a new text file at ``C:\Program Files (x86)\tor-win32\torrc`` and put this in it, replacing the ``HashedControlPassword`` with the one you just generated::

    ControlPort 9051
    HashedControlPassword 16:00322E903D96DE986058BB9ABDA91E010D7A863768635AC38E213FDBEF

In your administrator command prompt, install tor as a service using the appropriate ``torrc`` file you just created (see `here <https://2019.www.torproject.org/docs/faq.html.en#NTService>`_ for more information on doing this). Like this::

    tor.exe --service install -options -f "C:\Program Files (x86)\tor-win32\torrc"

You're now running a system Tor in Windows!

Open OnionShare. Click the Settings icon. Under "How should OnionShare connect to Tor?" choose "Connect using control port", and set the control port host to ``127.0.0.1`` and the port to ``9051``. Under "Tor authentication options" choose "Password" and set the password to your password, in my case ``comprised stumble rummage work avenging construct volatile``. Click the "Test Settings" button. If all goes well, you should see successfully connected to tor.

Using a system Tor in Mac OS X
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, install `Homebrew <http://brew.sh/>`_ if you don't already have it. Then, install Tor::

    brew install tor

Now configure Tor to allow connections from OnionShare::

    mkdir -p /usr/local/var/run/tor
    chmod 700 /usr/local/var/run/tor
    echo 'SOCKSPort 9050' >> /usr/local/etc/tor/torrc
    echo 'ControlPort unix:"/usr/local/var/run/tor/control.socket"' >> /usr/local/etc/tor/torrc

And start the system Tor service::

    brew services start tor

Open OnionShare. Click the Settings icon. Under "How should OnionShare connect to Tor?" choose "Connect using socket file", and set the socket file to be ``/usr/local/var/run/tor/control.socket``. Under "Tor authentication options" choose "No authentication, or cookie authentication". Click the "Test Settings" button. If all goes well, you should see successfully connected to tor.

Using a system Tor in Linux
^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, install the tor package. If you're using Debian, Ubuntu, or a similar Linux distro, I recommend you use Tor Project's `official repository <https://2019.www.torproject.org/docs/debian.html.en>`_. For example, in Ubuntu 20.04::

    sudo su -c "echo 'deb http://deb.torproject.org/torproject.org focal main' > /etc/apt/sources.list.d/torproject.list"
    curl https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --import
    gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install -y tor deb.torproject.org-keyring

Next, add your user to the group that runs the Tor process (in the case of Debian and Ubuntu, ``debian-tor``) and configure OnionShare to connect to your system Tor's control socket file.

Add your user to the ``debian-tor`` group by running this command (replace ``username`` with your actual username)::

    sudo usermod -a -G debian-tor username

Reboot your computer. After it boots up again, open OnionShare. Click the Settings icon. Under "How should OnionShare connect to Tor?" choose "Connect using socket file", and set the socket file to be ``/var/run/tor/control``. Under "Tor authentication options" choose "No authentication, or cookie authentication". Click the "Test Settings" button. If all goes well, you should see successfully connect to Tor.