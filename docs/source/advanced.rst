Advanced usage
==============

.. _save_tabs:

Save tabs
---------

By default, everything in OnionShare is temporary. As soon as you close an OnionShare tab its address no longer exists and can't be used again. But sometimes you might want an OnionShare service to be persistent. For example, this would be useful if you want to host a website that can keep the same URL even if you reboot your computer.

To make any tab persistent, check the "Save this tab, and automatically open it when I open OnionShare" box before starting the server. When a tab is saved a purple pin icon appears to the left of its server status.

.. image:: _static/screenshots/advanced-save-tabs.png

When you quit OnionShare and then open it again, your saved tabs will start out open. You'll have to manually start each service, but when you do they will start with the same OnionShare address, and with the same password.

If you save a tab, a copy of that tab's onion service secret key will be stored on your computer with your OnionShare settings.

.. _disable_passwords:

Disable passwords
-----------------

By default, all OnionShare services are protected with the username `onionshare` and a randomly-generated password. If someone makes 20 wrong guesses of the password, your onion service is automatically stopped to prevent a brute force attack against the OnionShare service.

But sometimes you might want your OnionShare service to be accessible to the public. For example, if you want to set up an OnionShare receive service so the public can securely and anonymously send you files. In this case, it's better to disable the password altogether. If you don't do this, someone can force your server to stop just by making 20 wrong guesses of your password, even if they know the correct password.

To disable the password for any tab, just check the "Don't use a password" box before starting the server. Then the server will be public and won't have a password.

Scheduled times
---------------

OnionShare supports scheduling exactly when a service should start and stop. Before starting server, click "Show advanced settings" in its tab and then check the boxes next to either "Start onion service at scheduled time", "Stop onion service at scheduled time", or both, and set the desired dates and times.

If you scheduled a service to start in the future, when you click the start button you will see a timer counting down until it will start. If you scheduled it to stop in the future, after it's started you will see a timer counting down to when it will stop automatically.

**Scheduling an OnionShare service to automatically start can be used as a dead man's switch**, where your service will be made public at a given time in the future if anything happens to you. If nothing happens to you, you can cancel the service before it's scheduled to start.

.. image:: _static/screenshots/advanced-schedule-start-timer.png

**Scheduling an OnionShare service to automatically stop can be useful to limit exposure**, like if you want to share secret documents while making sure they're not available on the internet for more than a few days.

.. image:: _static/screenshots/advanced-schedule-stop-timer.png

Legacy addresses
----------------

OnionShare uses v3 Tor onion services by default. These are modern onion addresses that have 56 characters, for example::

    uf3wmtpbstcupvrrsetrtct7qcmnqvdcsxqzxthxbx2y7tidatxye7id.onion

But it still has support for v2 onion addresses, the old type of onion addresses that have 16 characters, for example::

    lc7j6u55vhrh45eq.onion

OnionShare calls v2 onion addresses "legacy addresses". v3 onion addresses are more secure, and using legacy addresses is not recommended.

To use legacy addresses, before starting a server click "Show advanced settings" in its tab and check the "Use a legacy address (v2 onion service, not recommended)" box. In legacy mode you can optionally enable Tor client authentication. Once you start a server in legacy mode you cannot remove legacy mode in that tab. Instead you must start a separate service in a separate tab.

Tor Project plans to `completely deprecate v2 onion services <https://blog.torproject.org/v2-deprecation-timeline>`_ on October 15, 2021, and legacy onion services will soon be removed from OnionShare as well.
