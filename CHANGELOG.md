# OnionShare Changelog

## 0.6

* Brand new drag-and-drop GUI with ability to start and stop server
* Much cleaner code split into several files
* Support for sharing multiple files and folders at once, and automatically zips files before sharing
* Redesigned receiver HTML interface
* Waits for hidden service to be available before displaying URL
* Cleans up hidden service directory on exit
* Continuous integration with Travis
* Support for multiple downloads at once
* Fixed unicode-related filename and display bugs
* Warns that large files could take hours to send
* New translations
* Several misc. bugfixes
* Added code signing for Windows with Authenticode

## 0.5

* Removed webkit GUI altogether, and refactored GUI with native Qt widget
* In Tails, launches separate process as root for Tor control port and firewall stuff, everything else runs as amnesia
* Fixed itsdangerous dependency bug in Debian Wheezy and Tails
* Guesses content type of file, responds in HTTP header

## 0.4

* Fixed critical XSS bug that could deanonymize user: https://micahflee.com/2014/07/security-advisory-upgrade-to-onionshare-0-4-immediately/
* Added CSP headers in GUI to prevent any future XSS bugs from working
* Hash urandom data before using it, to avoid leaking state of entropy
* Constant time compare the slug to avoid timing attacks
* Cleaned up Tails firewall code

## 0.3

* Built a simple, featureful cross-platform GUI
* Graphical installers for Windows and OSX
* Packaged for Linux in .deb, .rpm, with desktop launcher
* Installable in Tails 1.1+, with simple "install" script
* Automatically copies URL to clipboard
* Automatically closes when download is done by default
* Shows download progress
* Limited suite of tests
* If a localized string doesn't exist, falls back to English
* New translations: Dutch, Portuguese, German, Russian, and updated translations: Norweigan, Spanish, French, Italian
