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

Build and publish to PyPi:

```
poetry publish --build
```