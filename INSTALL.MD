# Install

## Aptitude Package Requirements

The following Apt Packages need to be installed in order to run this application.

* python3 (at least 3.6)
* python3-dev
* python3-virtualenv
* python3-pip
* postgresql-9.3
* postgresql-server-dev-all
* build-essential
* libxml2
* libxml2-dev
* libxlst1-dev

`python3 python3-dev python3-virtualenv python3-pip postgresql-9.3 postgresql-server-dev-all build-essential libxml2 libxml2-dev libxlst1-dev`

## Setup Test Environment

`venv project`

`cd project; source bin/activate`

`git clone <repo_url> APIS`

`cd APIS`

`pip3 install wheel`

`pip3 install -r requirements.txt`


### POSTGRES Setup

`sudo su postgres`

`psql`

`CREATE USER fm_test_user WITH PASSWORD '<dbpass in settings.py>';`

`CREATE DATABASE fm_test;`

`GRANT ALL PRIVILEGES ON DATABASE fm_test TO fm_test_user;`

`\q`

`exit`

`python manage.py migrate`

`python manage.py createsuperuser`

`python manage.py runserver`

Login with your Super User credentials, Make a test event, then visit /registration/
