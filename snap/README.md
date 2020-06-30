# Snap package

This folder contains files to build a [snap package](https://snapcraft.io/). First make sure you install `snap` and `snapcraft` (`snap install snapcraft --classic`).

To build the snap, cd to the `snap` folder and run:

```sh
snapcraft
```

See your installed snaps:

```sh
snap list
```

Run the OnionShare snap:

```sh
/snap/bin/onionshare      # CLI version
/snap/bin/onionshare-gui  # GUI version
```

Delete the OnionShare snap:

```sh
snap remove onionshare
```
