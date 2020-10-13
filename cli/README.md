```
                     @@@@@@@@@                      
                @@@@@@@@@@@@@@@@@@@                 
             @@@@@@@@@@@@@@@@@@@@@@@@@              
           @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@           ___        _               
               @@@@@@         @@@@@@@@@@@@@         / _ \      (_)              
         @@@@    @               @@@@@@@@@@@       | | | |_ __  _  ___  _ __    
       @@@@@@@@                   @@@@@@@@@@       | | | | '_ \| |/ _ \| '_ \   
     @@@@@@@@@@@@                  @@@@@@@@@@      \ \_/ / | | | | (_) | | | |  
   @@@@@@@@@@@@@@@@                 @@@@@@@@@       \___/|_| |_|_|\___/|_| |_|  
      @@@@@@@@@                 @@@@@@@@@@@@@@@@    _____ _                     
      @@@@@@@@@@                  @@@@@@@@@@@@     /  ___| |                    
       @@@@@@@@@@                   @@@@@@@@       \ `--.| |__   __ _ _ __ ___ 
       @@@@@@@@@@@               @    @@@@          `--. \ '_ \ / _` | '__/ _ \
        @@@@@@@@@@@@@         @@@@@@               /\__/ / | | | (_| | | |  __/
         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@             \____/|_| |_|\__,_|_|  \___|
           @@@@@@@@@@@@@@@@@@@@@@@@@@@@@            
             @@@@@@@@@@@@@@@@@@@@@@@@@              
                @@@@@@@@@@@@@@@@@@@                 
                     @@@@@@@@@                      
```

# OnionShare CLI

_This project is under development and not ready for use._

OnionShare is an open source tool that lets you securely and anonymously share files, host websites, and chat with friends using the Tor network.

This is the command line version of OnionShare. [Click here](https://github.com/micahflee/onionshare) for the graphical version.

## Installing OnionShare CLI

First, make sure you have `tor` installed. In Linux, install it through your package manager. In macOS, install it with [Homebrew](https://brew.sh): `brew install tor`.

Then install OnionShare CLI:

```
pip install onionshare-cli
```

Then run it with:

```
onionshare-cli --help
```

## Developing OnionShare CLI

You must have python3 and [poetry](https://python-poetry.org/) installed.

Install dependencies with poetry:

```
poetry install
```

To run from the source tree:

```
poetry run onionshare-cli
```

To run tests:

```
poetry run pytest -vvv ./tests
```

### Making a release

Before making a release, make update the version in these places:

- `pyproject.toml`
- `onionshare_cli/resources/version.txt`

And edit `CHANGELOG.md` to include a list of all major changes since the last release.

Create a PGP-signed git tag. For example for OnionShare CLI 0.1.0, the tag must be `v0.1.0`.

Build and publish to PyPi:

```
poetry publish --build
```

Test status: [![CircleCI](https://circleci.com/gh/micahflee/onionshare-cli.svg?style=svg)](https://circleci.com/gh/micahflee/onionshare-cli)