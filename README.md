# OnionShare

[![Build Status](https://travis-ci.org/micahflee/onionshare.png)](https://travis-ci.org/micahflee/onionshare)

[OnionShare](https://onionshare.org) lets you securely and anonymously share files of any size. It works by starting a web server, making it accessible as a Tor Onion Service, and generating an unguessable URL to access and download the files. It does _not_ require setting up a separate server or using a third party file-sharing service. You host the files on your own computer and use a Tor Onion Service to make it temporarily accessible over the internet. The receiving user just needs to open the URL in Tor Browser to download the file.

## Documentation

To learn how OnionShare works, what its security properties are, and how to use it, check out the [wiki](https://github.com/micahflee/onionshare/wiki).

## Downloading Onionshare

You can download OnionShare for Windows and macOS from the [OnionShare website](https://onionshare.org). It should be available in your package manager for Linux, and it's included by default in [Tails](https://tails.boum.org).

## Developing OnionShare

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md). You may also subscribe to our developers mailing list [here](https://lists.riseup.net/www/info/onionshare-dev).

# Screenshots 

![Server Screenshot](/screenshots/server.png)
![Client Screenshot](/screenshots/client.png)
