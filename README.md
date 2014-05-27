# OnionShare

OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

![Screenshot](/screenshot.png)

## Quick Start

OnionShare works in GNU/Linux, Mac OS X, and Windows. The easiest way to install it right now is by using pip:

    sudo pip install onionshare

More detailed installation instructions for all platforms are coming soon.

## How to Use

OnionShare relies on Tor. You need to either have a system Tor installed (`sudo apt-get install tor`), or you can open Tor Browser so that OnionShare can use the Tor server provided there. Start Tor, and then run `onionshare`, passing in the file that you want to share, like this:

    [user@dev onionshare]$ onionshare ~/Desktop/secrets.pdf
    Connecting to Tor ControlPort to set up hidden service on port 26828

    Give this URL to the person you're sending the file to:
    http://v645bzpxmdtclpv3.onion/73b44511983c08bf29df40d0b1d00a69

    Press Ctrl-C to stop server

     * Running on http://127.0.0.1:26828/
    127.0.0.1 - - [21/May/2014 21:52:42] "GET /73b44511983c08bf29df40d0b1d00a69 HTTP/1.1" 200 -
    127.0.0.1 - - [21/May/2014 21:52:43] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [21/May/2014 21:52:44] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [21/May/2014 21:52:46] "GET /73b44511983c08bf29df40d0b1d00a69/download HTTP/1.1" 200 -

Securely send the URL to the person you are sending the file to (like by using Jabber and OTR). When they load the website in Tor Browser, they will be connecting directly to your computer to download the file. Once you confirm that they have downloaded the file you're sending (ask them if they have the file), press Ctrl-C to shut down the server.

### Using OnionShare in Tails

See [instructions here](/tails/README.md).

### Using OnionShare in Windows

OnionShare isn't properly packaged for Windows yet. This means you'll need to install Python 2.x yourself. [Download the latest 2.x version of python](https://www.python.org/downloads/) for your architecture and install it. Your python binary should be something like `C:\Python27\python.exe`.

Since OnionShare is a command line program, and using it involves copying and pasting a URL from a command prompt window, it's less frusturating if you use the Windows PowerShell rather than the Command Prompt (in PowerShell, select text you want to copy and then right-click to copy it onto the clipboard). But you can use either. Open either PowerShell or a Command Prompt, cd to your onionshare folder, and run `python.exe onionshare` with the path to the file you want to share. For example:

    PS C:\Users\user\Desktop\onionshare> C:\Python27\python.exe bin\onionshare C:\Users\user\Desktop\secrets.pdf
    Connecting to Tor ControlPort to set up hidden service on port 40867

    Give this URL to the person you're sending the file to:
    http://nkcdw6bgokit3tcn.onion/912d927863347b7b97f7a268a4210694

    Press Ctrl-C to stop server

     * Running on http://127.0.0.1:40867/
    127.0.0.1 - - [22/May/2014 11:30:55] "GET /912d927863347b7b97f7a268a4210694 HTTP/1.1" 200 -
    127.0.0.1 - - [22/May/2014 11:30:57] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [22/May/2014 11:30:57] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [22/May/2014 11:30:59] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [22/May/2014 11:31:02] "GET /912d927863347b7b97f7a268a4210694/download HTTP/1.1" 200 -
    127.0.0.1 - - [22/May/2014 11:31:14] "GET /912d927863347b7b97f7a268a4210694/download HTTP/1.1" 200 -

