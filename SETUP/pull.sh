#!/bin/sh
wall "Detected web hook on APIS..."
cd /home/dhickman/APIS/
sudo git pull
sudo python /home/dhickman/APIS/manage.py collectstatic --noinput
sudo python /home/dhickman/APIS/manage.py makemigrations --noinput
sudo python /home/dhickman/APIS/manage.py migrate --noinput
sudo systemctl restart apache2
