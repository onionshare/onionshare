Installation
============

Windows or macOS
----------------

You can download OnionShare for Windows and macOS from the `OnionShare website <https://onionshare.org/>`_.

For added security, see :ref:`verifying_sigs`.

.. _linux:

Linux with Flatpak
------------------

There are various ways to install OnionShare for Linux, but the recommended way is to use the Flatpak package. Flatpak ensures that you'll always use the latest dependencies and run OnionShare inside of a sandbox.

Make sure you have ``flatpak`` installed and the Flathub repository added by following `these instructions <https://flatpak.org/setup/>`_ for your Linux distribution.

Then install OnionShare from Flathub by following `the instructions here <https://flathub.org/apps/details/org.onionshare.OnionShare>`_.

.. _verifying_sigs:

Verifying PGP signatures
------------------------

You can verify that the Windows, macOS, or the source package you download is legitimate and hasn't been tampered with by verifying its PGP signature. For Windows and macOS, this step is optional and provides defense in depth: the installers also include their operating system-specific signatures, and you can just rely on those alone if you'd like.

Signing key
^^^^^^^^^^^

Windows, macOS, and source packages are signed by Micah Lee, the core developer, using his PGP public key with fingerprint ``927F419D7EC82C2F149C1BD1403C2657CD994F73``. You can download Micah's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/927F419D7EC82C2F149C1BD1403C2657CD994F73>`_.

You must have GnuPG installed to verify signatures. For macOS you probably want `GPGTools <https://gpgtools.org/>`_, and for Windows you probably want `Gpg4win <https://www.gpg4win.org/>`_.

Signatures
^^^^^^^^^^

You can find the signatures (``.asc`` files), as well as Windows, macOS, and source packages, at https://onionshare.org/dist/ in the folders named for each version of OnionShare. You can also find them on the `GitHub Releases page <https://github.com/micahflee/onionshare/releases>`_.

Verifying
^^^^^^^^^

Once you have imported Micah's public key into your GnuPG keychain, downloaded the binary, and downloaded the ``.asc`` signature, you can verify the binary for macOS in a terminal like this::

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

If you don't see 'Good signature from', there might be a problem with the integrity of the file (malicious or otherwise), and you should not install the package. (The WARNING shown above, is not a problem with the package: it only means you haven't already defined any level of 'trust' of Micah's PGP key.)

If you want to learn more about verifying PGP signatures, guides for `Qubes OS <https://www.qubes-os.org/security/verifying-signatures/>`_ and the `Tor Project <https://support.torproject.org/tbb/how-to-verify-signature/>`_ may be helpful.
