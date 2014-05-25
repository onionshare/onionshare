# OnionShare

OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

![Screenshot](/screenshot.png)

## Quick Start

At the moment OnionShare is a command line program. It works in Mac OS X, GNU/Linux, and Windows (see special Windows and Tails instructions below). To get started, either git clone the onionshare repository or [download this zip file](https://github.com/micahflee/onionshare/archive/master.zip) and extract it. Open a terminal and navigate to the  onionshare directory.

You can also install onionshare by using PIP or easy_instal. On pip you can type `pip install onionshare` and on easy_install your can use `easy_install onionshare`.

OnionShare relies on Tor. You need to either have a system Tor installed (`sudo apt-get install tor`), or you can open Tor Browser so that OnionShare can use the Tor server provided there. Start Tor, and then run `onionshare.py`, passing in the file that you want to share, like this:

    [user@dev onionshare]$ ./onionshare.py ~/Desktop/secrets.pdf 
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

## Using OnionShare in Windows

OnionShare isn't properly packaged for Windows yet. This means you'll need to install Python 2.x yourself. [Download the latest 2.x version of python](https://www.python.org/downloads/) for your architecture and install it. Your python binary should be something like `C:\Python27\python.exe`.

Since OnionShare is a command line program, and using it involves copying and pasting a URL from a command prompt window, it's less frusturating if you use the Windows PowerShell rather than the Command Prompt (in PowerShell, select text you want to copy and then right-click to copy it onto the clipboard). But you can use either. Open either PowerShell or a Command Prompt, cd to your onionshare folder, and run `python.exe onionshare.py` with the path to the file you want to share. For example:

    PS C:\Users\user\Desktop\onionshare> C:\Python27\python.exe onionshare.py C:\Users\user\Desktop\secrets.pdf
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

## Using OnionShare in Tails

You need to run OnionShare as root in Tails, so make sure you set an administrator password when you boot Tails. Follow the same instructions as above, except run `onionshare-tails` instead of `onionshare.py`, and run it with sudo like this:

    amnesia@amnesia:~/Persistent/code/onionshare$ sudo ./onionshare-tails ~/Persistent/file_to_send.pgp
    [sudo] password for amnesia:
    Connecting to Tor ControlPort to set up hidden service on port 16089
    Punching a hole in the firewall

In case you're wondering: OnionShare needs root in Tails in order to talk to the Tor ControlPort to create a new hidden service, and also so it can punch a hole in the rigid Tails firewall so that Tor can communicate with the local web server.
