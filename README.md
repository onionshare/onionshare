# OnionShare

[![Build Status](https://travis-ci.org/micahflee/onionshare.png)](https://travis-ci.org/micahflee/onionshare)

OnionShare lets you securely and anonymously share files of any size. It works by starting a web server, making it accessible as a Tor onion service, and generating an unguessable URL to access and download the files. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor onion service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

Features include:

* A user-friendly drag-and-drop graphical user interface that works in Windows, Mac OS X, and Linux
* Ability to share multiple files and folders at once
* Support for multiple people downloading files at once
* Automatically copies the unguessable URL to your clipboard
* Shows you the progress of file transfers
* When file is done transferring, automatically closes OnionShare to reduce the attack surface
* Localized into several languages, and supports international unicode filenames

If you're interested in exactly what OnionShare does and does not protect against, read the [Security Design Document](/SECURITY.md).

![Client Screenshot](/screenshots/client.png)
![Server Screenshot](/screenshots/server.png)

## Quick Start

Check out [the wiki](https://github.com/micahflee/onionshare/wiki) for information about how to use OnionShare and it's various features.

You can download OnionShare to install on your computer from <https://onionshare.org/>.

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md).
