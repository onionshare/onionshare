# OnionShare

OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

![Screenshot](/screenshot.png)

OnionShare 0.3 is under active development and will be released soon. Features include:

* A user-friendly GUI interface that works in Windows, Mac OS X, and Linux
* Automatically copies the unguessable URL to your clipboard
* Displays log of all requests, so you can see when someone is accessing your OnionShare service, or if someone is trying to guess your secret URL
* Shows you the progress of the file transfer
* When file is done transferring, automatically closes OnionShare to reduce the attack surface

## Quick Start

You can install OnionShare 0.3dev right now by following [these instructions](/BUILD.md). You can install OnionShare 0.3 in your Tails persistent volume by following [these instructions](/tails/README.md) (requires Tails 1.1 or later).

You can also install the command-line only version using pip: `sudo pip install onionshare`. When 0.3 is released the pip version will no longer be updated.

## How to Use

Before you can share a file, you need to open [Tor Browser](https://www.torproject.org/) in the background. This will provide the Tor service that OnionShare uses to start the hidden service.

Open OnionShare and browse to find the file you wish to share. It will show you a long, random-looking URL such as `http://v645bzpxmdtclpv3.onion/73b44511983c08bf29df40d0b1d00a69` and copy it to your clipboard. This is the secret URL that can be used to download the file you're sharing. If you'd like multiple people to be able to download this file, uncheck the "close automatically" checkbox in the corner.

Send this URL to the person you're trying to send the file to. If the file you're sending isn't very secret, you can use use normal means of sending the URL: emailing it, posting it to Facebook or Twitter, etc. If you're trying to send a secret file then it's important to send this URL secrely. I recommend you use [Off-the-Record encrypted chat](https://pressfreedomfoundation.org/encryption-works#otr) to send the URL.

