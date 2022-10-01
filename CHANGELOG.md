# OnionShare Changelog

## 2.6

* Major feature: a new 'Quickstart' screen, which enables toggling on or off an animated automatic connection to Tor. This allows configuring network settings prior to automatic connection.
* Major feature: Censorship circumvention. Use new features in the upstream Tor API to try to automatically obtain bridges depending on the user's location.
* New feature: automatically fetch the built-in bridges from the upstream Tor API rather than hardcode them in each release of OnionShare.
* New feature: keyboard shortcuts to access various modes and menus, and accessibility hints
* Bug fix: Temporary Directory for serving the OnionShare web pages was broken on Windows
* Miscellaneous: many dependency updates, web page theming improvements, and packaging automation improvements.


## 2.5

* Security fix: Sanitize the path parameter in History item widget to be plain text
* Security fix: Use microseconds in Receive mode directory creation to avoid potential DoS
* Security fix: Several hardening improvements for session and username management in Chat mode, to prevent impersonation and other issues
* Major feature: Obtain bridges from Moat / BridgeDB (over a domain-fronted Meek client)
* Major feature: Snowflake bridge support
* New feature: Tor connection settings, as well as general settings, are now Tabs rather than dialogs
* New feature: User can customize the Content-Security-Policy header in Website mode
* New feature: Built-in bridges are automatically updated from Tor's API when the user has chosen to use them
* Switch to using our `stem` fork called `cepa`, which is now published on Pypi so we can build it in releases
* Various bug fixes

## 2.4

* Major feature: Private keys (v3 onion client authentication) replaces passwords and HTTP basic auth
* Updated Tor to 0.4.6.7 on all platforms
* Various bug fixes

## 2.3.3

* New feature: Setting for light or dark theme
* Updated Tor to 0.4.6.7 for Linux, 0.4.5.10 for Windows and macOS
* Various bug fixes

## 2.3.2

* New feature: Custom titles can be set for OnionShare's various modes
* New feature: Receive mode supports notification webhooks
* New feature: Receive mode supports submitting messages as well as files
* New feature: New ASCII art banner and prettier verbose output
* New feature: Partial support for range requests (pausing and resuming in HTTP)
* Updated Tor to 0.4.5.7
* Updated built-in obfs4 bridges
* Various bug fixes

## 2.3.1

* Bugfix: Fix chat mode
* Bugfix: Fix --persistent in onionshare-cli
* Bugfix: Fix checking for updates in Windows and macOS

## 2.3

* Major new feature: Multiple tabs, including better support for persistent services, faster Tor connections
* New feature: Chat anonymously mode
* New feature: All new design
* New feature: Ability to display QR codes of OnionShare addresses
* New feature: Web apps have responsive design and look better on mobile
* New feature: Flatpak and Snapcraft packaging for Linux
* Several bug fixes

## 2.2

* New feature: Website mode, which allows publishing a static HTML website as an onion service
* Allow individual files to be viewed or downloaded in Share mode, including the ability to browse into subdirectories and use breadcrumbs to navigate back
* Show a counter when individual files or pages are viewed
* Better History items including colors and status codes to differentiate between successful and failed requests
* Swap out the random /slug suffix for HTTP basic authentication (when in non-public mode)
* Hide the Tor connection settings if the ONIONSHARE_HIDE_TOR_SETTINGS environment variable is set (Tails compatibility)
* Remove the NoScript XSS warning in Receive Mode now that the NoScript/Tor Browser bug is fixed. The ajax upload method still exists when javascript is enabled.
* Better support for DragonFly BSD
* Updated various dependencies, including Flask, Werkzeug, urllib3, requests, and PyQt5
* Updated Tor to 0.4.1.5
* Other minor bug fixes
* New translations:
  * Arabic (العربية)
  * Dutch (Nederlands)
  * Persian (فارسی)
  * Romanian (Română)
  * Serbian latin (Srpska (latinica))
* Removed translations with fewer than 90% of strings translated:
  * Finnish (Suomi)

## 2.1

* New feature: Auto-start timer, which allows scheduling when the server starts
* Renamed CLI argument --debug to --verbose
* Make Tor connection timeout configurable as a CLI argument
* Updated various dependencies, including fixing third-party security issues in urllib3, Jinja2, and jQuery
* Updated Tor to 0.3.5.8
* New translations:
  * Traditional Chinese (正體中文 (繁體)),
  * Simplified Chinese (中文 (简体))
  * Finnish (Suomi)
  * German (Deutsch)
  * Icelandic (Íslenska)
  * Irish (Gaeilge)
  * Norwegian Bokmål (Norsk bokmål)
  * Polish (Polski)
  * Portuguese Portugal (Português (Portugal))
  * Telugu (తెలుగు)
  * Turkish (Türkçe)
  * Ukrainian (Українська)
* Removed translations with fewer than 90% of strings translated:
  * Bengali (বাংলা)
  * Persian (فارسی)

## 2.0

* New feature: Receiver mode allows you to receive files with OnionShare, instead of only sending files
* New feature: Support for next generation onion services
* New feature: macOS sandbox is enabled
* New feature: Public mode feature, for public uses of OnionShare, which when enabled turns off slugs in the URL and removes the limit on how many 404 requests can be made
* New feature: If you're sharing a single file, don't zip it up
* New feature: Full support for meek_lite (Azure) bridges
* New feature: Allow selecting your language from a dropdown
* New translations: Bengali (বাংলা), Catalan (Català), Danish (Dansk), French (Français), Greek (Ελληνικά), Italian (Italiano), Japanese (日本語), Persian (فارسی), Portuguese Brazil (Português Brasil), Russian (Русский), Spanish (Español), Swedish (Svenska)
* Several bugfixes
* Invisible to users, this version includes some major refactoring of the codebase, and a robust set of unit tests which makes OnionShare easier to maintain going forward

## 1.3.2

* Bugfix: In debug mode, stop saving flask debug log in /tmp, where all users can access it

## 1.3.1

* Updated Tor to 0.2.3.10
* Windows and Mac binaries are now distributed with licenses for Tor and obfs4

## 1.3

* Major UI redesign, introducing many UX improvements
* Client-side web interface redesigned
* New feature: Support for meek_lite pluggable transports (Amazon and Azure) - not yet ready for Windows or macOS, sorry
* New feature: Support for custom obfs4 and meek_lite bridges (again, meek_lite not available on Windows/macOS yet)
* New feature: Ability to cancel share before it starts
* Bugfix: The UpdateChecker no longer blocks the UI when checking
* Bugfix: Simultaneous downloads (broken in 1.2)
* Updated Tor to 0.2.3.9
* Improved support for BSD
* Updated French and Danish translations
* Minor build script and build documentation fixes
* Flake8 tests added

## 1.2

* New feature: Support for Tor bridges, including obfs4proxy
* New feature: Ability to use a persistent URL
* New feature: Auto-stop timer, to stop OnionShare at a specified time
* New feature: Get notification when Tor connection dies
* Updated versions of Python, Qt, Tor, and other dependencies that are bundled
* Added ability to supply a custom settings file as a command line arg
* Added support for FreeBSD
* Fixed small user interface issues
* Fixed minor bugs
* New Dutch translations

## 1.1

* OnionShare connects to Tor itself now, so opening Tor Browser in the background isn't required
* In Windows and macOS, OnionShare alerts users about updates
* Removed the menu bar, and adding a "Settings" button
* Added desktop notifications, and a system tray icon
* Ability to add multiple files and folders with a single "Add" button
* Ability to delete multiple files and folders at once with the "Delete" button
* Hardened some response headers sent from the web server
* Minor clarity improvements to the contents of the share's web page
* Alert the user rather than share an empty archive if a file was unreadable
* Prettier progress bars

## 1.0

* Fixed long-standing macOS X bug that caused OnionShare to crash on older Macs (!)
* Added settings dialog to configure connecting to Tor, including support for system Tor
* Added support for stealth onion services (advanced option)
* Added support for Whonix
* Improved AppArmor profiles
* Added progress bar for zipping up files
* Improved the look of download progress bars
* Allows developers to launch OnionShare from source tree, without building a package
* Deleted legacy code, and made OnionShare purely use ephemeral Tor onion services
* Switched to EFF's diceware wordlist for slugs

## 0.9.2 (Linux only)

* Looks for `TOR_CONTROL_PORT` environment variable, to help Tails integration
* Change how OnionShare checks to see if it's installed system-wide, to help Subgraph OS integration

## 0.9.1

* Added Nautilus extension, so you can right-click on a file and choose "Share via OnionShare", thanks to Subgraph developers
* Switch to using the term "onion service" rather than "hidden service"
* Fix CVE-2016-5026, minor security issue related to use of /tmp directory
* Switch from PyInstaller to cx_Freeze for Windows and OSX packaging
* Support CLI in Windows and OSX

## 0.9

* Slugs are now shorter and human-readable, with rate limiting to prevent URL guessing
* Uses a new slug each time the server restarts
* "Stop sharing automatically" enforces only one download
* Users get asked if they're sure they want to close OnionShare while server is running
* Added estimated time remaining progress indicator
* Fixed frozen window while waiting for hidden service to start
* Displays version number in both GUI and CLI
* Closing window causes downloads to stop immediately
* Web server listens in ports 17600-17650, for future Tails support
* Updated translations
* Ported from Python 2 to Python 3 and from Qt4 to Qt5
* Ported from py2app and py2exe to PyInstaller

## 0.8.1

* Fixed crash in Windows 7
* Fixed crash related to non-ephemeral hidden services in Linux
* Fixed minor bugs

## 0.8

* Add support for ephemeral hidden services
* Stopped leaking sender's locale on download page
* Add support for Tor Messenger as provider of Tor service
* Minor bugfixes, code cleanup, and refactoring

## 0.7.1

* Fixed critical bug in OS X binaries that caused crashes on some computers
* Added Security Design document
* Minor bugfix with Windows code signing timestamp server
* Linux version uses HS dir that is allowed by Tor Browser Launcher's AppArmor profiles

## 0.7

* Added code signing for Mac OS X
* Does not disable existing hidden services
* Uses allowZip64 to allow compressing files >5gb
* Sets HS dir to be in /var/lib/tor in Tails, to obey AppArmor rules
* Misc. minor code cleanup

## 0.6

* Brand new drag-and-drop GUI with ability to start and stop server
* Much cleaner code split into several files
* Support for sharing multiple files and folders at once, and automatically compresses files before sharing
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
* New translations: Dutch, Portuguese, German, Russian, and updated translations: Norwegian Bokmål, Spanish, French, Italian
