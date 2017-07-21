django-seuranta
===============

Live gps tracking server for orienteering events.

[![Build Status](https://travis-ci.org/rphlo/django-seuranta.svg?branch=master)](https://travis-ci.org/rphlo/django-seuranta)
[![Coverage Status](https://coveralls.io/repos/rphlo/django-seuranta/badge.svg?branch=dev)](https://coveralls.io/r/rphlo/django-seuranta?branch=dev)


Requirement
-----------

Python version 3.4


Installation
------------

First create a ```local_settings.py``` file in ```/seuranta/app/``` folder to indicates your db and smtp settings, secret key and allowed host according to standard django settings. See django documentation for more detials.

You can then run ```./install.sh``` It will ask for a username and a password for a super user that you can use to login in the admin.

Once installed you can run the server with ```python manage.py runserver``` admin is available at ```http://127.0.0.1:8000/admin/```

In the admin configure the site at ```http://127.0.0.1:8000/admin/sites/site/``` and your facebook app detail in ```http://127.0.0.1:8000/admin/socialaccount/socialapp/```

It is recomended to run the application as uwsgi app behind a nginx server. Search for ```django with uwsgi and nginx``` for tutorials.

To use the web tracker and use the user location you will need to run the application with HTTPS. You can get a free certificate with lets encrypt or run behing a proxy such as Cloudflare.
