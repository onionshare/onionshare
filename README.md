# OnionShare

[OnionShare](https://onionshare.org) lets you securely and anonymously share files of any size. It works by starting a web server, making it accessible as a Tor Onion Service, and generating an unguessable URL to access and download the files. It does _not_ require setting up a separate server or using a third party file-sharing service. You host the files on your own computer and use a Tor Onion Service to make it temporarily accessible over the internet. The receiving user just needs to open the URL in Tor Browser to download the file.

## Documentation

To learn how OnionShare works, what its security properties are, and how to use it, check out the [wiki](https://github.com/micahflee/onionshare/wiki).

## Downloading OnionShare

You can download OnionShare for Windows and macOS from the [OnionShare website](https://onionshare.org).

For Ubuntu-like distributions, you could use this PPA to get the latest version:

```
sudo add-apt-repository ppa:micahflee/ppa
sudo apt install -y onionshare
```

OnionShare also may be available in your operating system's package manager:

[![Packaging status](https://repology.org/badge/vertical-allrepos/onionshare.svg)](https://repology.org/metapackage/onionshare/versions)

## Developing OnionShare

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md). You may also subscribe to our developers mailing list [here](https://lists.riseup.net/www/info/onionshare-dev).

Test status: [![CircleCI](https://circleci.com/gh/micahflee/onionshare.svg?style=svg)](https://circleci.com/gh/micahflee/onionshare)

# Screenshots

![Share mode OnionShare](/screenshots/onionshare-share-server.png)

![Share mode Tor Browser](/screenshots/onionshare-share-client.png)

![Receive mode OnionShare](/screenshots/onionshare-receive-server.png)

![Receive mode Tor Browser](/screenshots/onionshare-receive-client.png)
