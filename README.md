# APIS EventManager

Data Model: http://www.gliffy.com/go/publish/10890219

Registrtion Workflows: http://www.gliffy.com/go/publish/10892367

Proposed Stack:
  + Ubuntu 18.04 (LTS)
  + Apache2
  + Postgres 9
  + Python 2.7.6
  + Django 1.11.16
  + Bootstrap 3.3.7
  + JQuery 1.9.1

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
    virtualenv -p python2 venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Review your settings
    cp fm_eventmanager/settings.py.dev fm_eventmanager/settings.py
    
    python manage.py migrate
    python manage.py createsuperuser

    # Create a self-signed certificate if you want to test or hack on U2F
    openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
      -keyout localhost.key -out localhost.crt -subj /CN=localhost

    # Get it running (omit --cert localhost for HTTP)
    python manage.py runserver_plus --cert localhost.crt

[square]: https://square.com/
[android]: https://github.com/furthemore/APIS-register
