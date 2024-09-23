Setup

# Contributing to OnionShare

## Prerequisites

1. Python 3
2. Poetry
3. Tor _(package; you would also need tor browser is needed for desktop)_
4. Go _(for desktop)_

## Setting Up the Codebase
Clone the repository:
   ```bash
   git clone https://github.com/onionshare/onionshare.git
   cd onionshare
   ```
### 1. Setting Up the CLI (Required for Desktop)

 Follow the setup instructions in `cli/Readme.md`:
   ```bash
   cd cli
   poetry install
   ```

### 2. Setting Up the Desktop

Navigate to the Desktop directory and follow the setup instructions in `desktop/Readme.md`:
   ```bash
   cd ../desktop
   poetry install
   ```

### 3. Running OnionShare

Run the desktop application:
```bash
poetry run onionshare-gui
```

Make sure `Tor` is running before starting OnionShare:
```bash
tor
```

## Contribution Guidelines

1. Fork the repository and create a branch from `main`.
2. Write clear commit messages.
3. Run tests before submitting a pull request (PR).
4. Open a PR to the main branch.
5. Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
