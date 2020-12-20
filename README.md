# APIS EventManager
[![Build Status](https://travis-ci.com/furthemore/APIS.svg?branch=production)](https://travis-ci.com/furthemore/APIS) [![Coverage Status](https://coveralls.io/repos/github/furthemore/APIS/badge.svg?branch=production)](https://coveralls.io/github/furthemore/APIS?branch=production)

Data Model snapshot (7 December 2020): https://i.imgur.com/A4fPDf5.png

Stack:
  + Ubuntu 20.04 (LTS)
  + Apache2
  + Postgres 11
  + Python 3.7
  + Django 1.11
  + Bootstrap 3
  + jQuery 1.9

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

![Screenshot of Cash Register Position](https://i.imgur.com/8vB1m0q.png)

## Quick start
To see a demo, or set up the project for development locally:

    git clone https://github.com/furthemore/APIS.git
    cd APIS
    python3 -v venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Review your settings
    cp fm_eventmanager/settings.py.devel fm_eventmanager/settings.py

    python manage.py migrate
    python manage.py createsuperuser

    # Create a self-signed certificate if you want to test or hack on U2F
    openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
      -keyout localhost.key -out localhost.crt -subj /CN=localhost

    # Get it running (omit --cert localhost for HTTP)
    python manage.py runserver_plus --cert localhost.crt

[square]: https://square.com/
[android]: https://github.com/furthemore/APIS-register

## Development
Note: Commit hook utilities require Python 3 to run.

### Using [pre-commit](https://pre-commit.com/)
1. Install: `pip install pre-commit` or `brew install pre-commit`.
2. then run: `pre-commit install`, this will apply the hooks defined in `.pre-commit-config.yaml` to evey commit

If you get errors about Python 2.7 when running pre-commit command, try deleting your pre-commit cache:

```sh
rm -rf ~/.cache/pre-commit
```
