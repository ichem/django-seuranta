#! /usr/bin/env bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
echo "To start a server use:"
echo "python manage.py runserver"