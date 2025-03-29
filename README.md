# APIS EventManager

![Build](https://github.com/furthemore/APIS/actions/workflows/django.yml/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/furthemore/APIS/badge.svg)](https://coveralls.io/github/furthemore/APIS)

Data Model snapshot (7 December 2020): https://i.imgur.com/A4fPDf5.png

Stack:
  + Ubuntu 20.04 (LTS)
  + Postgres
  + Python 3.12+
  + Django 5.1
  + Bootstrap 3
  + jQuery 1.12

## Features
  + Take payments for pre-registration using [Square][square], both online
    and in-person with an [Android app][android] as a customer-facing
    display, with cash drawer and receipt printer integration.
  + Manage staff registration and department heirarchies.
  + Handle dealer applications, registration, and payments.
  + Create limited-use discounts.
  + Handle on-site registration on your own kiosks, or via a public URL.
  + Populate attendee information by scanning their ID with a simple
    [browser worker](https://github.com/rechner/py-aamva).
  + Print badges on the fly with a custom template on any compatible card
    or label printer, with Unicode-supported fonts (Emoji!)
  + Protect admin and volunteer logins with TOTP 2-Factor or FIDO U2F.

![Screenshot of Cash Register Position](https://i.imgur.com/7iJSS8E.png)

## Quick start
### Running Using Published Docker Images

    # Install docker using the instructions at either:
    # https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04 or
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
    git clone https://github.com/furthemore/APIS.git
    cd APIS

    # Create .env from template and edit relevant settings (API keys, etc)
    cp example.env .env

    # You’ll need a Square developer account to take payments: https://squareup.com/signup?country_code=us&v=developers
    # If your hosting provider is not configured for a mail relay, you’ll want to populate these lines with SMTP account credentials with e.g. gmail or mailgun.

    # Install make and other necessary utilities
    apt install build-essential

    # Install docker using the instructions at either:
    # https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04 or
    # https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository.

    # Build base docker image:
    make build-base-docker-image

    # Edit Dockerfile and replace the first line with output from last command. (The console will remind you.)

    # Give yourself permission to run Docker commands
    sudo usermod -aG docker ${USER}
    # Log out and back in to make it take effect

    # Build final image
    make build-docker-image

    # Run in Docker
    docker compose up -d

    # Create Superuser
    docker compose exec app /app/manage.py createsuperuser
    # Respond to prompts as needed

    # OPTIONAL: If you intend to run APIS in production, configure your webserver to act as a reverse proxy.
    # Example docs: https://www.digitalocean.com/community/tutorials/how-to-use-apache-as-a-reverse-proxy-with-mod_proxy-on-ubuntu-16-04

    # Run the development server
    make dev

    # Go to http://localhost:8000/registration/ in a web browser and follow the directions.

### Locally without docker (recommended for developers)

This repository leverages nix and direnv on Linux systems (Including WSL2) to automatically setup the dev environment.

* Install Nix: https://nixos.org/download/
* Install direnv: https://direnv.net/docs/installation.html

This project leverages [Poetry](https://python-poetry.org/) for dependency management and packaging.

#### Manual development environment setup

If you cannot use Nix and direnv (e.g. native Windows filesystem), perform the following steps:

1. Install [Git](https://git-scm.com/downloads) and [Python 3.12+](https://www.python.org/downloads/) if they aren't already installed.
2. Install [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer).
    * Make sure that the directory containing the poetry script is added to your PATH after installation - check the command line output for instructions after Poetry is installed!
3. Clone the repository.
4. Install dependencies:

```
poetry sync
poetry env activate
```

5. Run the command output after `poetry env activate` to activate the python venv.
6. Set up the development server settings:

```
cp convention_event_manager_django_site/settings.py.devel convention_event_manager_django_site/settings.py
```

7. Set up the development database and a super admin account:

```
python manage.py migrate
python manage.py createsuperuser
```

8. Run the server!

```
python manage.py runserver
```

#### Run with a self-signed certificate

To test functionality over HTTPS, you'll need to create a self-signed certificate and run the server with it using a different commmand:

```
# Create a self-signed certificate if you want to test or hack on U2F
openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
    -keyout localhost.key -out localhost.crt -subj /CN=localhost

# Get it running (omit --cert localhost for HTTP)
python manage.py runserver_plus --cert localhost.crt
```

[square]: https://square.com/
[android]: https://github.com/furthemore/APIS-register

## Development

### Using [pre-commit](https://pre-commit.com/)
1. Install: `pip install pre-commit` or `brew install pre-commit`.
2. then run: `pre-commit install`, this will apply the hooks defined in `.pre-commit-config.yaml` to evey commit

```
