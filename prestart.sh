#!/bin/bash

./manage.py migrate
./manage.py collectstatic
