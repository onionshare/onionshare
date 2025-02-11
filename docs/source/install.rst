Installation
============

Windows or macOS
----------------

You can download OnionShare for Windows and macOS from the `OnionShare website <https://onionshare.org/>`_.

.. _linux:

Mobile
----------------

You can download OnionShare for Mobile from the follow links

* Android
	* Google Play: https://play.google.com/store/apps/details?id=org.onionshare.android
	* F-Droid: https://github.com/onionshare/onionshare-android-nightly

* iOS
	* Apple App Store: https://apps.apple.com/app/onionshare/id1601890129
	* Direct IPA download: https://github.com/onionshare/onionshare-ios/releases
	* Testflight: https://testflight.apple.com/join/ZCJeY65W


Linux
-----

There are various ways to install OnionShare for Linux, but the recommended way is to use either the `Flatpak <https://flatpak.org/>`_ or the `Snap <https://snapcraft.io/>`_ package.
Flatpak and Snapcraft ensure that you'll always use the newest version and run OnionShare inside of a sandbox.

Snapcraft support is built-in to Ubuntu and Fedora comes with Flatpak support, but which you use is up to you. Both work in all Linux distributions.

**Install OnionShare using Flatpak**: https://flathub.org/apps/details/org.onionshare.OnionShare

**Install OnionShare using Snapcraft**: https://snapcraft.io/onionshare

You can also download and install PGP-signed ``.flatpak`` or ``.snap`` packages from https://onionshare.org/dist/ if you prefer.

Manual Flatpak Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd like to install OnionShare manually with Flatpak using the PGP-signed `single-file bundle <https://docs.flatpak.org/en/latest/single-file-bundles.html>`_, you can do so like this:

- Install Flatpak by following the instructions at https://flatpak.org/setup/.
- Add the Flathub repository by running ``flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo``. Even though you won't be downloading OnionShare from Flathub, OnionShare depends on some packages that are only available there.
- Go to https://onionshare.org/dist/, choose the latest version of OnionShare, and download the ``.flatpak`` and ``.flatpak.asc`` files.
- Verify the PGP signature of the ``.flatpak`` file. See :ref:`verifying_sigs` for more info.
- Install the ``.flatpak`` file by running ``flatpak install OnionShare-VERSION.flatpak``. Replace ``VERSION`` with the version number of the file you downloaded.

You can run OnionShare with: `flatpak run org.onionshare.OnionShare`.

Manual Snapcraft Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd like to install OnionShare manually with Snapcraft using the PGP-signed Snapcraft package, you can do so like this:

- Install Snapcraft by following the instructions at https://snapcraft.io/docs/installing-snapd.
- Go to https://onionshare.org/dist/, choose the latest version of OnionShare, and download the ``.snap`` and ``.snap.asc`` files.
- Verify the PGP signature of the ``.snap`` file. See :ref:`verifying_sigs` for more info.
- Install the ``.snap`` file by running ``snap install --dangerous onionshare_VERSION_amd64.snap``. Replace ``VERSION`` with the version number of the file you downloaded. Note that you must use `--dangerous` because the package is not signed by the Snapcraft store, however you did verify its PGP signature, so you know it's legitimate.

You can run OnionShare with: `snap run onionshare`.

.. _pip:

Command-line only
-----------------

You can install just the command-line version of OnionShare on any operating system using the Python package manager ``pip``. :ref:`cli` has more info.

.. _freebsd:

FreeBSD
-------

Althought not being officially developed for this platform, OnionShare can also be installed on `FreeBSD <https://freebsd.org/>`_. It's available via its ports collection or as pre-built package. Should you opt to install and use OnionShare on a FreeBSD operating system, please be aware that it's **NOT** officially supported by the OnionShare project.

Though not being offered and officially maintained by the OnionShare developers, the FreeBSD packages and ports do fetch and verifies the source codes from the official OnionShare repository (or its official release packages from `PyPI <https://pypi.org/project/onionshare-cli/>`_). Should you wish to check changes related to this platform, please refer to the following resources:

- https://cgit.freebsd.org/ports/log/www/onionshare
- https://www.freshports.org/www/onionshare

Manual pkg Installation
^^^^^^^^^^^^^^^^^^^^^^^

To install the binary package, use ``pkg install pyXY-onionshare``, with ``pyXY`` specifying the version of Python the package was built for. So, in order to install OnionShare for Python 3.9, use::

    pkg install py39-onionshare

There's also a **Command-line only** version of OnionShare available as pre-built package. Replace ``py39-onionshare`` by ``py39-onionshare-cli`` if you want to install that version.

For additional information and details about the FreeBSD pre-built packages, please refer to its `official Handbook section about pkg <https://docs.freebsd.org/en/books/handbook/ports/#pkgng-intro>`_.

Manual port Installation
^^^^^^^^^^^^^^^^^^^^^^^^

To install the FreeBSD port, change directory to the `ports collection <https://freebsd.org/ports/>`_ you must have checked out before and run the following::

    make -s -C www/onionshare all install clean

The ports collection also offers a dedicated port for the **Command-line only** version of OnionShare. Replace ``www/onionshare`` by ``www/onionshare-cli`` if you want to install that version.

For additional information and details about the FreeBSD ports collection, please refer to its `official Handbook section about ports <https://docs.freebsd.org/en/books/handbook/ports/#ports-using>`_.

.. _verifying_sigs:

Verifying PGP signatures
------------------------

You can verify that the package you download is legitimate and hasn't been tampered with by verifying its PGP signature.
For Windows and macOS, this step is optional and provides defense in depth: the OnionShare binaries include operating system-specific signatures, and you can just rely on those alone if you'd like.

Signing key
^^^^^^^^^^^

Packages are signed by the core developer who is responsible for the particular release. Here is the GPG
key information for each of the core developers of OnionShare:

* Micah Lee:
    * PGP public key fingerprint ``927F419D7EC82C2F149C1BD1403C2657CD994F73``.
    * You can download Micah's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/927F419D7EC82C2F149C1BD1403C2657CD994F73>`_.

* Saptak Sengupta:
    * PGP public key fingerprint ``2AE3D40A6905C8E4E8ED95ECE46A2B977C14666B``.
    * You can download Saptak's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/2AE3D40A6905C8E4E8ED95ECE46A2B977C14666B>`_.

* Miguel Jacq:
    * PGP public key fingerprint ``00AE817C24A10C2540461A9C1D7CDE0234DB458D``.
    * You can download Miguel's key `from the keys.openpgp.org keyserver <https://keys.openpgp.org/vks/v1/by-fingerprint/00AE817C24A10C2540461A9C1D7CDE0234DB458D>`_.

You must have GnuPG installed to verify signatures. For macOS you probably want `GPGTools <https://gpgtools.org/>`_, and for Windows you probably want `Gpg4win <https://www.gpg4win.org/>`_.

Signatures
^^^^^^^^^^

You can find the signatures (as ``.asc`` files), as well as Windows, macOS, Flatpak, Snap, and source packages, at https://onionshare.org/dist/ in the folders named for each version of OnionShare.
You can also find them on the `GitHub Releases page <https://github.com/onionshare/onionshare/releases>`_.

Verifying
^^^^^^^^^

Once you have imported the core developers public keys into your GnuPG keychain, downloaded the binary and ``.asc`` signature, you can verify the binary in a terminal like this:

For Windows::

    gpg --verify OnionShare-win64-2.6.msi.asc OnionShare-win64-2.6.msi (Windows 64-bit)

For macOS::

    gpg --verify OnionShare-2.6.dmg.asc OnionShare-2.6.dmg

For Linux::

    gpg --verify OnionShare-2.6.flatpak.asc OnionShare-2.6.flatpak (Flatpak)

    gpg --verify onionshare_2.6_amd64.snap.asc onionshare_2.6_amd64.snap (Snap)

and for the source file::

    gpg --verify onionshare-2.6.tar.gz.asc onionshare-2.6.tar.gz

The expected output looks like this::

    gpg: Signature made Mo 10 Okt 2022 02:27:16 CEST
    gpg:                using RSA key 927F419D7EC82C2F149C1BD1403C2657CD994F73
    gpg: Good signature from "Micah Lee <micah@micahflee.com>" [unknown]
    gpg:                 aka "Micah Lee <micah.lee@firstlook.media>" [unknown]
    gpg: WARNING: This key is not certified with a trusted signature!
    gpg:          There is no indication that the signature belongs to the owner.
    Primary key fingerprint: 927F 419D 7EC8 2C2F 149C  1BD1 403C 2657 CD99 4F73

If you don't see ``Good signature from``, there might be a problem with the integrity of the file (malicious or otherwise), and you should not install the package.

The ``WARNING:`` shown above, is not a problem with the package, it only means you haven't defined a level of "trust" of Micah's (the core developer) PGP key.

If you want to learn more about verifying PGP signatures, the guides for `Qubes OS <https://www.qubes-os.org/security/verifying-signatures/>`_ and the `Tor Project <https://support.torproject.org/tbb/how-to-verify-signature/>`_ may be useful.
