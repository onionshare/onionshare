Connecting to Tor
=================

Pick a way to connect OnionShare to Tor by clicking the "⚙" icon in the bottom right of the OnionShare window to get to its settings.

.. image:: _static/screenshots/settings.png

Use the Tor bundled with OnionShare
-----------------------------------

This is the default, simplest and most reliable way that OnionShare connects to Tor.
For this reason, it's recommended for most users.

When you open OnionShare, it launches an already configured Tor process in the background OnionShare to use.
It doesn't interfere with other Tor processes on your computer, so you can use the Tor Browser or the system Tor on their own.

Attempt auto-configuration with Tor Browser
------------------------------------------------

If you have `downloaded the Tor Browser <https://www.torproject.org>`_ and don't want two Tor processes running, you can use the Tor process from the Tor browser.
Keep in mind you need to keep Tor Browser open in the background while you're using OnionShare for this to work.

Using a system Tor in Windows
-----------------------------

This is fairly advanced. You'll need to know how edit plaintext files and do stuff as an administrator.

Download the Tor Windows Expert Bundle `from <https://www.torproject.org/download/tor/>`_.
Extract the ZIP file and copy the extracted folder to ``C:\Program Files (x86)\``
Rename the extracted folder with ``Data`` and ``Tor`` in it to ``tor-win32``.

Make up a control port password.
(Using 7 words in a sequence like ``comprised stumble rummage work avenging construct volatile`` is a good idea for a password.)
Now open a command prompt (cmd) as an administrator, and use ``tor.exe --hash-password`` to generate a hash of your password. For example::

    cd "C:\Program Files (x86)\tor-win32\Tor"
    tor.exe --hash-password "comprised stumble rummage work avenging construct volatile"

The hashed password output is displayed after some warnings (which you can ignore). In the case of the above example, it is ``16:00322E903D96DE986058BB9ABDA91E010D7A863768635AC38E213FDBEF``.

Now create a new text file at ``C:\Program Files (x86)\tor-win32\torrc`` and put your hashed password output in it, replacing the ``HashedControlPassword`` with the one you just generated::

    ControlPort 9051
    HashedControlPassword (The numbers you generate from the password you picked above)

In your administrator command prompt, install Tor as a service using the appropriate ``torrc`` file you just created (as described in `<https://2019.www.torproject.org/docs/faq.html.en#NTService>`_). Like this::

    tor.exe --service install -options -f "C:\Program Files (x86)\tor-win32\torrc"

You are now running a system Tor process in Windows!

Open OnionShare. Under "How should OnionShare connect to Tor?" choose "Connect using control port", and set
"Control port" to ``127.0.0.1`` and
"Port" to ``9051``.
Under "Tor authentication options" choose "Password" and set the password to the control port password you picked above
Click the "Test Connection to Tor" button.
If all goes well, you should see "Connected to the Tor controller".

Using the system's Tor in macOS
-------------------------------

First, install `Homebrew <https://brew.sh/>`_ if you don't already have it. Then, install Tor::

    brew install tor

Now configure Tor to allow connections from OnionShare::

    mkdir -p /usr/local/var/run/tor
    chmod 700 /usr/local/var/run/tor
    echo 'SOCKSPort 9050' >> /usr/local/etc/tor/torrc
    echo 'ControlPort unix:"/usr/local/var/run/tor/control.socket"' >> /usr/local/etc/tor/torrc

And start the system Tor service::

    brew services start tor

Open OnionShare and click the "⚙" icon in it.
Under "How should OnionShare connect to Tor?" choose "Connect using socket file", and
set the socket file to be ``/usr/local/var/run/tor/control.socket``.
Under "Tor authentication options" choose "No authentication, or cookie authentication".
Click the "Test Connection to Tor" button.

If all goes well, you should see "Connected to the Tor controller".

Using the system's Tor in Linux
-------------------------------

First, install the Tor package. If you're using Debian, Ubuntu, or a similar Linux distro, It is recommended to use the Tor Project's `official repository <https://2019.www.torproject.org/docs/debian.html.en>`_. For example, in Ubuntu 20.04::

    sudo su -c "echo 'deb https://deb.torproject.org/torproject.org focal main' > /etc/apt/sources.list.d/torproject.list"
    curl https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --import
    gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install -y tor deb.torproject.org-keyring

Next, add your user to the group that runs the Tor process (in the case of Debian and Ubuntu, ``debian-tor``) and configure OnionShare to connect to your system Tor's control socket file.

Add your user to the ``debian-tor`` group by running this command (replace ``username`` with your actual username)::

    sudo usermod -a -G debian-tor username

Reboot your computer.
After it boots up again, open OnionShare and click the "⚙" icon in it.
Under "How should OnionShare connect to Tor?" choose "Connect using socket file".
Set the socket file to be ``/var/run/tor/control``.
Under "Tor authentication options" choose "No authentication, or cookie authentication".
Click the "Test Settings" button.

If all goes well, you should see "Connected to the Tor controller".

Using Tor bridges
-----------------

If your access to the Internet is censored, you can configure OnionShare to connect to the Tor network using `Tor bridges <https://2019.www.torproject.org/docs/bridges.html.en>`_. If OnionShare connects to Tor without one, you don't need to use a bridge.

To configure bridges, click the "⚙" icon in OnionShare.

You can use the built-in obfs4 pluggable transports, the built-in meek_lite (Azure) pluggable transports, or custom bridges, which you can obtain from Tor's `BridgeDB <https://bridges.torproject.org/>`_.
If you need to use a bridge, try the built-in obfs4 ones first.
