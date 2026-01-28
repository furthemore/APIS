# APIS EventManager

![Build](https://github.com/furpocalypse/APIS/actions/workflows/django.yml/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/furpocalypse/APIS/badge.svg)](https://coveralls.io/github/furpocalypse/APIS)

Data Model snapshot (7 December 2020): https://i.imgur.com/A4fPDf5.png

Stack:
  + Ubuntu 22.04 (LTS)
  + Python 3.14
  + Django 6.0
  + PostgreSQL 16.10
  + Bootstrap 3/jQuery 1.12
  + SolidJS
  + MQTT event passing

## Features
  + Take payments for pre-registration using [Square][square], both online
    and in-person with an [iPad app][ipad] as a customer-facing
    display, with cash drawer and receipt printer integration.
  + Manage staff registration and department hierarchies.
  + Handle dealer applications, registration, and payments.
  + Create limited-use discounts.
  + Handle on-site registration on your own kiosks, or via a public URL.
  + Populate attendee information by scanning their ID.
  + Print badges on the fly with a custom template on any compatible card
    or label printer, with Unicode-supported fonts (Emoji!)
  + Protect admin and volunteer logins with TOTP 2-Factor or FIDO U2F.

![Screenshot of Cash Register Position](/docs/admin-onsite.png)

## Quick start
### Running Using Published Docker Images

    # Install docker using the instructions at either:
    # https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04 or
    # https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository.

    # Download docker-compose.yml and example.env files from this repo

    # Create .env from template and edit relevant settings (API keys, etc)
    cp example.env .env

    # You’ll need a Square developer account to take payments: https://squareup.com/signup?country_code=us&v=developers
    # If your hosting provider is not configured for a mail relay, you’ll want to populate these lines with SMTP account credentials with e.g. gmail or mailgun.

    # Run in Docker
    docker compose up -d

    # Create superuser account
    docker compose exec app /app/manage.py createsuperuser
    # Respond to prompts as needed

    # Go to http://localhost:8000/registration/ in a web browser and follow the setup directions.

## Development Environment Setup
### Building Docker Container
The following was tested on a fresh installation of Ubuntu 20.04.

    # Get the software from Github
    git clone https://github.com/furpocalypse/APIS.git
    cd APIS

    # Create .env from template and edit relevant settings (API keys, etc)
    cp example.env .env

    # You’ll need a Square developer account to take payments: https://squareup.com/signup?country_code=us&v=developers
    # If your hosting provider is not configured for a mail relay, you’ll want to populate these lines with SMTP account credentials with e.g. gmail or mailgun.

    # Install make and other necessary utilities
    apt install build-essential

    # Install docker using the instructions at either:
    # https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04 or
    # https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository.

    # Give yourself permission to run Docker commands
    sudo usermod -aG docker ${USER}
    # Log out and back in to make it take effect

    # Build image
    make build-docker-image

    # Run in Docker
    docker compose up -d

    # Create Superuser
    docker compose exec app /app/manage.py createsuperuser
    # Respond to prompts as needed

    # Run the development server
    make dev

    # Go to http://localhost:8000/registration/ in a web browser and follow the directions.

### Locally without docker (recommended for developers)

The recommended development environment is Linux, or WSL if you're on Windows. If on Linux, you can install [direnv] to streamline your environment setup and management. All instructions below assume you've freshly cloned the repository but have NOT entered the new directory yet.

#### Automatic setup with direnv

If you have installed `direnv`, environment setup and dependency installation should be handled for you by entering the project directory after you allow direnv load the `/envrc` file.

    direnv allow ./APIS

Make a copy of `development.env` to `.env`, then put the needed configuration and secrets into the file:

    cp ./APIS/development.env ./APIS/.env
    nano ./APIS/.env #Or use whatever your favorite editor is

Then copy the settings file template tailored for direnv use, modify other settings if desired, and enter the directory. uv will install itself, set up a python venv, install all dependencies, load config into environment variables, and install pre-commit hooks:

    cp ./APIS/fm_eventmanager/settings.py.direnv ./APIS/fm_eventmanager/settings.py
    cd APIS

#### Manual setup

APIS uses [uv][uv] for project configuration, dependency management, and virtual environment configuration. Install it as per [its documentation][uv-install]:

    # Linux/WSL using curl
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Linux/WSL using wget
    wget -qO- https://astral.sh/uv/install.sh | sh

    # Windows without WSL
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Next, copy the development settings file template for development and make any changes you need to configure the database, mail server, Square, etc

    # Linux
    cp ./APIS/fm_eventmanager/settings.py.devel ./APIS/fm_eventmanager/settings.py

    # Windows
    Copy-Item .\APIS\fm_eventmanager\settings.py.devel .\APIS\fm_eventmanager\settings.py

Next, enter the directory, set up the python virtual environment, and install dependencies with uv:

    # Linux
    cd APIS
    uv venv
    source .venv/bin/activate
    uv sync

    # Windows
    Set-Location APIS
    uv venv
    .venv\Scripts\activate
    uv sync

Finally, set up pre-commit hooks:

    uv tool run pre-commit install

Be sure to run `deactivate` when finished to close the python venv!

#### First run

After getting everything set up by either method above, set up the Postgres database and run migrations to set it up, create the superuser, and then launch the server.

**NOTE**: Recent versions of Debian and its derivatives (e.g. Ubuntu, Linux Mint) package Postgres in a way that allows multiple versions to run concurrently, thus the binaries that these scripts use aren't on the PATH. You will need to set up your Postgres instance manually, make sure the database name, user, and password are set in the config (or the `.env` file if using direnv), and skip to the `migrate` command in this case.

    # Create and start the development database server (except on Debian)
    python manage.py make_db
    python manage.py start_db

    # Set up database tables, create the admin user, and run the server.
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

You should be able to access the APIS instance at http://127.0.0.1:8000 with the superuser account you created.

### Production use
For production use you will also need an MQTT broker for some features like taking on-site payments with the iPad application.
Please see [this documentation](https://github.com/furthemore/APIS/wiki/MQTT-Configuration) for notes about configuring a broker.

## Development

### Using [pre-commit](https://pre-commit.com/)
1. Install: `pip install pre-commit` or `brew install pre-commit`.
2. then run: `pre-commit install`, this will apply the hooks defined in `.pre-commit-config.yaml` to evey commit

[square]: https://square.com/
[ipad]: https://github.com/furthemore/APIS-Register-Swift
[android]: https://github.com/furthemore/APIS-register
[direnv]: https://direnv.net/
[uv]: https://docs.astral.sh/uv/
[uv-install]: https://docs.astral.sh/uv/#installation
