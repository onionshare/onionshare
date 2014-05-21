# OnionShare

A program to securely share a file of any size with someone, designed to be run in Tails. It works by starting a web server, making it accessible as a Tor hidden service, and making it require a password to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. It all just runs inside Tails and uses the Tor network.

![Screenshot](/screenshot.png)

## Quick Start

### If you're using Tails

You need to run OnionShare as root in Tails, so make sure you set an administrator password when you boot Tails. First, get a copy of the OnionShare program:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

To run it, use the onionshare-tails script:

    amnesia@amnesia:~/Persistent/code/onionshare$ sudo ./onionshare-tails ~/Persistent/file_to_send.pgp
    [sudo] password for amnesia:
    Connecting to Tor ControlPort to set up hidden service on port 16089
    Punching a hole in the firewall

    Give this information to the person you're sending the file to:
    URL: http://muqi5o5dfdraj2ms.onion/
    Username: f3bce5f2b373906f
    Password: 866b2f1a710ece73

    Press Ctrl-C to stop server

     * Running on http://127.0.0.1:16089/
    127.0.0.1 - - [21/May/2014 18:47:42] "GET / HTTP/1.1" 401 -
    127.0.0.1 - - [21/May/2014 18:47:52] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [21/May/2014 18:47:55] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [21/May/2014 18:47:55] "GET /favicon.ico HTTP/1.1" 404 -

Securely send the URL, username, and password to the person you are sending the file to (like by using Jabber and OTR). When they load the website, they will be connecting directly to your computer. They'll need the username and password to authenticate. You can watch all the web requests that are getting made.

Once you confirm that they have downloaded the file you're sending (ask them), press Ctrl-C to shut down the server and clean up your Tails setup.

    127.0.0.1 - - [21/May/2014 18:48:50] "GET /download HTTP/1.1" 200 -
    ^C

    Closing hole in firewall

### If you're using other operating systems

Non-Tails operating systems coming soon.
