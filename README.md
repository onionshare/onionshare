# OnionShare

[![Build Status](https://travis-ci.org/micahflee/onionshare.png)](https://travis-ci.org/micahflee/onionshare)

OnionShare lets you securely and anonymously share files of any size. It works by starting a web server, making it accessible as a Tor onion service, and generating an unguessable URL to access and download the files. It doesn't require setting up a server on the internet somewhere or using a third party file-sharing service. You host the file on your own computer and use a Tor onion service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

**To learn how OnionShare works, what its security properties are, and how to use it, check out the [wiki](https://github.com/micahflee/onionshare/wiki).**

**You can download OnionShare for Windows and macOS from <https://onionshare.org/>. It should be available in your package manager for Linux, and it's included by default in Tails.**

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md).

-![Client Screenshot](/screenshots/client.png)
-![Server Screenshot](/screenshots/server.png)
