# Running OnionShare in Tails

Until OnionShare gets included in Debian, it will be annoying to install it in Tails so that it persists reboots. For now, you'll need to run a build script the first time, and then run a setup script after each boot. The OnionShare GUI works in Tails 1.1 and later.

### Building for Tails

Start by booting to Tails. Mount your persistent volume and set an administrator password. Once you login and connect to the Tor network, open a terminal and type:

    cd ~/Persistent
    git clone https://github.com/micahflee/onionshare.git
    cd onionshare
    sudo tails/build.sh

You only need to do that once each time you want to build a new verison of OnionShare.

### Installing in Tails

In order to actually use it though, each time you boot Tails you'll need to enable your persistent volume, set an administrator password, and run this:

    cd ~/Persistent/onionshare
    sudo tails/setup.sh

After running that, OnionShare will appear in the menu under Applications > Internet.

