# OnionShare

A program to securely share a file of any size with someone, designed to be run in Tails. It works by starting a web server, making it accessible as a Tor hidden service, and making it require a password to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. It all just runs inside Tails and uses the Tor network.

![Screenshot](/screenshot.png)

## Quick Start

You need to run this script as root, so make sure you set an administrator password when you boot Tails. Run onionshare.py, and pass it a filename. It will look something like this:

    amnesia@amnesia:~/Persistent/code/onionshare$ sudo ./onionshare.py ~/Persistent/file_to_send.gpg
    [sudo] password for amnesia:
    Modifying torrc to configure hidden service on port 41710
    Reloading tor daemon configuration...                                                   [  DONE  ]
    Punching a hole in the firewall
    Waiting 10 seconds for hidden service to get configured...

    Give this information to the person youre sending the file to:
    URL: http://b6vgwkuo77qieguy.onion/
    Username: 5eebeba8b70cfdfc
    Password: f5a7fa91c294479a

    Press Ctrl-C to stop server

     * Running on http://127.0.0.1:41710/
    127.0.0.1 - - [20/May/2014 19:41:19] "GET / HTTP/1.1" 401 -
    127.0.0.1 - - [20/May/2014 19:41:28] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [20/May/2014 19:41:31] "GET /favicon.ico HTTP/1.1" 404 -
    127.0.0.1 - - [20/May/2014 19:41:31] "GET /favicon.ico HTTP/1.1" 404 -

Securely send the URL, username, and password to the person you are sending the file to (like by using Jabber and OTR). When they load the website, they will be connecting directly to your computer. They'll need the username and password to authenticate. You can watch all the web requests that are getting made.

Once you confirm that they have downloaded the file you're sending (ask them), press Ctrl-C to shut down the server and clean up your Tails setup.

    Restoring original torrc
    Reloading tor daemon configuration...                                                   [  DONE  ]
    Closing hole in firewall

