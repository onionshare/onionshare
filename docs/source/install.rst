Installation
============

Windows or macOS
----------------

You can download OnionShare for Windows and macOS from the `OnionShare website <https://onionshare.org/>`_.

.. _linux:

Linux
-----

There are various ways to install OnionShare for Linux, but the recommended way is to use either the `Flatpak <https://flatpak.org/>`_ or the `Snap <https://snapcraft.io/>`_ package.
Flatpak and Snapcraft ensure that you'll always use the newest version and run OnionShare inside of a sandbox.

Snapcraft support is built-in to Ubuntu and Fedora comes with Flatpak support, but which you use is up to you. Both work in all Linux distributions.

**Install OnionShare using Flatpak**: https://flathub.org/apps/details/org.onionshare.OnionShare

**Install OnionShare using Snapcraft**: https://snapcraft.io/onionshare

You can also download and install PGP-signed ``.flatpak`` or ``.snap`` packages from https://onionshare.org/dist/ if you prefer.

.. _pip:

Command-line only
-----------------

You can install just the command-line version of OnionShare on any operating system using the Python package manager ``pip``. :ref:`cli` has more info.

.. _verifying_sigs:

Verifying PGP signatures
------------------------

You can verify that the package you download is legitimate and hasn't been tampered with by verifying its PGP signature.
For Windows and macOS, this step is optional and provides defense in depth: the OnionShare binaries include operating system-specific signatures, and you can just rely on those alone if you'd like.

Signing key
^^^^^^^^^^^

Packages are signed by Micah Lee, the core developer, using his PGP public key with fingerprint ``927F419D7EC82C2F149C1BD1403C2657CD994F73``.
You can download Micah's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/927F419D7EC82C2F149C1BD1403C2657CD994F73>`_.

You must have GnuPG installed to verify signatures. For macOS you probably want `GPGTools <https://gpgtools.org/>`_, and for Windows you probably want `Gpg4win <https://www.gpg4win.org/>`_.

Signatures
^^^^^^^^^^

You can find the signatures (as ``.asc`` files), as well as Windows, macOS, Flatpak, Snap, and source packages, at https://onionshare.org/dist/ in the folders named for each version of OnionShare.
You can also find them on the `GitHub Releases page <https://github.com/micahflee/onionshare/releases>`_.

Verifying
^^^^^^^^^

Once you have imported Micah's public key into your GnuPG keychain, downloaded the binary and and ``.asc`` signature, you can verify the binary for macOS in a terminal like this::

    gpg --verify OnionShare-2.2.pkg.asc OnionShare-2.2.pkg

Or for Windows, in a command-prompt like this::

    gpg.exe --verify onionshare-2.2-setup.exe.asc onionshare-2.2-setup.exe

The expected output looks like this::

    gpg: Signature made Tue 19 Feb 2019 09:25:28 AM AEDT using RSA key ID CD994F73
    gpg: Good signature from "Micah Lee <micah@micahflee.com>"
    gpg:                 aka "Micah Lee <micah@firstlook.org>"
    gpg:                 aka "Micah Lee <micah@freedom.press>"
    gpg:                 aka "Micah Lee <micah.lee@firstlook.org>"
    gpg:                 aka "Micah Lee <micah.lee@theintercept.com>"
    gpg: WARNING: This key is not certified with a trusted signature!
    gpg:          There is no indication that the signature belongs to the owner.
    Primary key fingerprint: 927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73

If you don't see ``Good signature from``, there might be a problem with the integrity of the file (malicious or otherwise), and you should not install the package. (The ``WARNING:`` shown above, is not a problem with the package, it only means you haven't defined a level of "trust" of Micah's (the core developer) PGP key.)

If you want to learn more about verifying PGP signatures, the guides for `Qubes OS <https://www.qubes-os.org/security/verifying-signatures/>`_ and the `Tor Project <https://support.torproject.org/tbb/how-to-verify-signature/>`_ may be useful.
