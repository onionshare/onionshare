# Running OnionShare in Tails

It's tricky to get all of the correct python dependencies in [Tails](https://tails.boum.org/). Until OnionShare is properly packaged in Debian (and their dependencies, flask and stem, are also packaged in the version of Debian that Tails is based on) and can just be [auto-installed on boot](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index13h2), this is a hack to get it working.

Run the `tails-onionshare` binary in this folder as root, and OnionShare will use the libraries in the lib folder so they don't have to be installed system-wide.

    amnesia@amnesia:~/Persistent/onionshare/tails$ sudo ./tails-onionshare /home/amnesia/Persistent/secrets.pdf
    [sudo] password for amnesia:
    Calculating SHA1 checksum.
    Connecting to Tor control port to set up hidden service on port 39465.
    Punching a hole in the firewall.

    Give this URL to the person you're sending the file to:
    http://sq64tkg4fxoscwns.onion/42b60c759a1ae438337dc797e910b60e

    Press Ctrl-C to stop server
     * Running on http://127.0.0.1:39465/
    127.0.0.1 - - [27/May/2014 21:05:32] "GET /42b60c759a1ae438337dc797e910b60e HTTP/1.1" 200 -
    127.0.0.1 - - [27/May/2014 21:05:36] "GET /favicon.ico HTTP/1.1" 200 -
    127.0.0.1 - - [27/May/2014 21:05:36] "GET /favicon.ico HTTP/1.1" 200 -

