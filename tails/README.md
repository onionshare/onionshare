# Running OnionShare in Tails

Until OnionShare gets included in Debian, it will be annoying to install it in Tails so that it persists reboots. For now, you'll need to run a build script the first time, and then install it separately each time you boot. These instructions make it pretty simple.

*The OnionShare GUI works in Tails 1.1 and later.*

### Building for Tails the first time

Start by booting to Tails. Mount your persistent volume and set an administrator password. Once you login and connect to the Tor network, open a terminal and type:

    cd ~/Persistent
    git clone https://github.com/micahflee/onionshare.git
    sudo onionshare/tails/build.sh

You only need to do that once each time you want to build a new verison of OnionShare.

### Installing in Tails

In order to actually use it though, each time you boot Tails you'll need to enable your persistent volume and set an administrator password. Then open your Persistent folder and double-click on `Install OnionShare`. Type your temporary administrator password, and then OnionShare will get installed.

OnionShare will appear in the menu under Applications > Internet > OnionShare.

