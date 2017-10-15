# Install

## Aptitude Package Requirements

The following Apt Packages need to be installed in order to run this application.

* python (2.7)
* python-dev
* python-virtualenv
* python-pip
* postgresql-9.3
* postgresql-server-dev-9.3
* build-essential
* libxml2
* libxml2-dev
* libxlst1-dev

`python python-dev python-virtualenv python-pip postgresql-9.3 postgresql-server-dev-9.3 build-essential libxml2 libxml2-dev libxlst1-dev`

## Setup Test Environment

`virtualenv project`

`cd project; source bin/activate`

`git clone <repo_url>`

`cd APIS`

`pip install -r requirements.txt`

NOTE: The version of payeezy in pip must be replaced with https://github.com/alsaihn/payeezy_direct_API to allow for passing addresses with payment information

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
