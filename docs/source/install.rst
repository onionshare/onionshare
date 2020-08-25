Installation
============

.. _flatpak:

Flatpak Instructions
--------------------

There are various ways to install OnionShare for Linux, but the recommended way is to use the Flatpak package. Flatpak ensures that you'll always use the most latest dependencies and run OnionShare inside of a sandbox.

Make sure you have ``flatpak`` installed and the Flathub repository added by following `these instructions <https://flatpak.org/setup/>`_ for your Linux distribution.

Then install OnionShare from Flathub by following `the instructions here <https://flathub.org/apps/details/org.onionshare.OnionShare>`_.

.. _verifying_sigs:

Verifying PGP Signatures
------------------------

You can verify that the Windows, macOS, or source package you download is legitimate and hasn't been tampered with by verifying its PGP signature. For Windows and macOS, this step is optional and provides defense in depth: the installers also include their operating system-specific signatures, and you can just rely on those alone if you'd like.

Signing Key
^^^^^^^^^^^

Windows, macOS, and source packaged are signed by Micah Lee, the core developer, using his PGP public key with fingerprint ``927F419D7EC82C2F149C1BD1403C2657CD994F73``. You can download Micah's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/927F419D7EC82C2F149C1BD1403C2657CD994F73>`_.

In order to verify signatures, you must have GnuPG installed. For macOS you probably want `GPGTools <https://gpgtools.org/>`_, and for Windows you probably want `Gpg4win <https://www.gpg4win.org/>`_.

Signatures
^^^^^^^^^^

You can find the signatures (``.asc`` files), as well as Windows, macOS, and source packages, at https://onionshare.org/dist/ in the folders named for each version of OnionShare. You can also find them on the `GitHub Releases page <https://github.com/micahflee/onionshare/releases>`_.

Verifying
^^^^^^^^^

Once you have imported Micah's public key into your GnuPG keychain, downloaded the binary, and downloaded the ``.asc`` signature, you can verify the binary for macOS in terminal like this::

    gpg --verify OnionShare-2.2.pkg.asc OnionShare-2.2.pkg

Or for Windows in a command prompt like this::

    gpg.exe --verify onionshare-2.2-setup.exe.asc onionshare-2.2-setup.exe

An expected output might look like this::

    gpg: Signature made Tue 19 Feb 2019 09:25:28 AM AEDT using RSA key ID CD994F73
    gpg: Good signature from "Micah Lee <micah@micahflee.com>"
    gpg:                 aka "Micah Lee <micah@firstlook.org>"
    gpg:                 aka "Micah Lee <micah@freedom.press>"
    gpg:                 aka "Micah Lee <micah.lee@firstlook.org>"
    gpg:                 aka "Micah Lee <micah.lee@theintercept.com>"
    gpg: WARNING: This key is not certified with a trusted signature!
    gpg:          There is no indication that the signature belongs to the owner.
    Primary key fingerprint: 927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73

If you don't see 'Good signature from', then there might be a problem with the integrity of the file (malicious or otherwise), and you perhaps should not install the package. (The WARNING shown above, is not a problem with the package: it only means you have not defined any level of 'trust' regarding Micah's PGP key itself.)

If you want to learn more about verifying PGP signatures, guides for `Qubes OS <https://www.qubes-os.org/security/verifying-signatures/>`_ and the `Tor Project <https://2019.www.torproject.org/docs/verifying-signatures.html.en>`_ may be helpful.