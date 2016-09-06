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

You can download OnionShare to install on your computer from <https://onionshare.org/>.

You can set up your development environment to build OnionShare yourself by following [these instructions](/BUILD.md).

## How to Use

Before you can share files, you need to open [Tor Browser](https://www.torproject.org/) in the background. This will provide the Tor service that OnionShare uses to start the onion service.

Open OnionShare and drag and drop files and folders you wish to share, and click Start Sharing. It will show you a .onion URL such as `http://asxmi4q6i7pajg2b.onion/egg-cain` and copy it to your clipboard. This is the secret URL that can be used to download the file you're sharing. If you'd like multiple people to be able to download this file, uncheck the "close automatically" checkbox.

Send this URL to the person you're trying to send the files to. If the files you're sending aren't secret, you can use normal means of sending the URL: emailing it, posting it to Facebook or Twitter, etc. If you're trying to send secret files then it's important to send this URL securely.

The person who is receiving the files doesn't need OnionShare. All they need is to open the URL you send them in Tor Browser to be able to download the file.

## Using the command line version

In Linux: Just run `onionshare` from the terminal.

In Windows: Add `C:\Program Files (x86)\OnionShare` to your PATH. Now you can run `onionshare.exe` in a command prompt.

In Mac OS X: Run `ln -s /Applications/OnionShare.app/Contents/MacOS/onionshare /usr/local/bin`. Now you can run `onionshare` from the terminal.
