isort = poetry run isort onionshare_cli tests
black = poetry run black onionshare_cli tests
flake8 = poetry run flake8 onionshare_cli tests

install:
	pip install poetry
	poetry install

run:
	poetry run onionshare-cli

test:
	poetry run pytest -v ./tests

build:
	poetry build

format:
	$(isort)
	$(black)

lint:
	$(flake8)
	$(isort) --check-only --df
	$(black) --check --diff