# OnionShare

[OnionShare](https://onionshare.org) is an open source tool for securely and anonymously sending and receiving files using Tor onion services. It works by starting a web server directly on your computer and making it accessible as an unguessable Tor web address that others can load in Tor Browser to download files from you, or upload files to you. It doesn't require setting up a separate server, using a third party file-sharing service, or even logging into an account. Unlike services like email, Google Drive, DropBox, WeTransfer, or nearly any other way people typically send files to each other, when you use OnionShare you don't give any companies access to the files that you're sharing. So long as you share the unguessable web address in a secure way (like pasting it in an encrypted messaging app), _no one_ but you and the person you're sharing files with can access them.

## Documentation

To learn how OnionShare works, what its security properties are, and how to use it, check out the [wiki](https://github.com/micahflee/onionshare/wiki).

## Downloading OnionShare

You can download OnionShare for Windows and macOS from the [OnionShare website](https://onionshare.org).

For Ubuntu-like Linux distributions, you could use this PPA to get the latest version:

```
sudo add-apt-repository ppa:micahflee/ppa
sudo apt install -y onionshare
```

OnionShare may also be available in your Linux distribution's package manager. Check [this wiki page](https://github.com/micahflee/onionshare/wiki/How-Do-I-Install-Onionshare) for more information.

## Contributing to OnionShare

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md). You may also subscribe to our mailing list [here](https://lists.riseup.net/www/info/onionshare-dev), and join our public Keybase team [here](https://keybase.io/team/onionshare).

Test status: [![CircleCI](https://circleci.com/gh/micahflee/onionshare.svg?style=svg)](https://circleci.com/gh/micahflee/onionshare)

# Screenshots

![Share mode OnionShare](/screenshots/onionshare-share-server.png)

![Share mode Tor Browser](/screenshots/onionshare-share-client.png)

![Receive mode OnionShare](/screenshots/onionshare-receive-server.png)

![Receive mode Tor Browser](/screenshots/onionshare-receive-client.png)
