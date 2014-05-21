# OnionShare

OnionShare is a program to securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and making it require credentials to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.

![Screenshot](/screenshot.png)

## Quick Start

At the moment OnionShare is a command line program. It works in normal desktop GNU/Linux distributions, Tails, and Mac OS X. To get started, either git clone the onionshare repository or [download a this zip file](https://github.com/micahflee/onionshare/archive/master.zip) and extract it. Open a terminal and navigate to the  onionshare directory.

OnionShare relies on Tor. You need to either have a system Tor installed (`sudo apt-get install tor`), or you can open Tor Browser so that OnionShare can use the Tor server provided there. Start Tor, and then run `onionshare.py`, passing in the file that you want to share, like this:

    [user@dev onionshare]$ ./onionshare.py ~/secret_files.zip
    Connecting to Tor ControlPort to set up hidden service on port 51439

    Give this information to the person you're sending the file to:
    URL: http://ryrvuliyyqv5qann.onion/
    Username: 0aa7d7266ca05753
    Password: d3e6eabad14ea7ad

    Press Ctrl-C to stop server

     * Running on http://127.0.0.1:51439/
    127.0.0.1 - - [21/May/2014 15:48:50] "GET / HTTP/1.1" 401 -
    127.0.0.1 - - [21/May/2014 15:48:59] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [21/May/2014 15:49:01] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [21/May/2014 15:49:02] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [21/May/2014 15:49:03] "GET /download HTTP/1.1" 200 -

Securely send the URL, username, and password to the person you are sending the file to (like by using Jabber and OTR). When they load the website, they will be connecting directly to your computer to download the file. They'll need the username and password to authenticate. Once you confirm that they have downloaded the file you're sending (ask them if they have the file), press Ctrl-C to shut down the server.

## Using OnionShare in Tails

You need to run OnionShare as root in Tails, so make sure you set an administrator password when you boot Tails. Follow the same instructions as above, except run `onionshare-tails` instead of `onionshare.py`, and run it with sudo like this:

    amnesia@amnesia:~/Persistent/code/onionshare$ sudo ./onionshare-tails ~/Persistent/file_to_send.pgp
    [sudo] password for amnesia:
    Connecting to Tor ControlPort to set up hidden service on port 16089
    Punching a hole in the firewall

In case you're wondering: OnionShare needs root in Tails in order to talk to the Tor ControlPort to create a new hidden service, and also so it can punch a hole in the rigid Tails firewall so that Tor can communicate with the local web server.
