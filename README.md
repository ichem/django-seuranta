django-seuranta
===============

Live gps tracking server for orienteering events.

[![Build Status](https://travis-ci.org/rphlo/django-seuranta.svg?branch=dev)](https://travis-ci.org/rphlo/django-seuranta)
[![Coverage Status](https://coveralls.io/repos/rphlo/django-seuranta/badge.svg?branch=dev)](https://coveralls.io/r/rphlo/django-seuranta?branch=dev)


Requirement
-----------

Python version 2.7


Installation
------------

run ```./install.sh```


API Endpoints
-------------

  * /api/time
   GET -- Return Server Unix Time

  * /api/auth_token/obtain
   POST -- Return user authorization token
   parameters
   ----------
    - username
    - password

  * /api/auth_token/destroy
   POST -- Void user authorization token
   parameters
   ----------
    - username
    - password

  * /api/competitor_token/obtain
   POST -- Return competitor publishing token
   parameters
   ----------
    - competitor
    - access_code

  * /api/competitor_token/destroy
   POST -- Void competitor publishing token
   params:
    - competitor
    - access_code

  * /api/competition
   GET
   POST

  * /api/competition/*competition_id*
   GET
   UPDATE
   DELETE

  * /api/map/*competition_id*[.jpg]
   GET
   UPDATE

  * /api/competitor
   GET
   POST

  * /api/competitor/*competitor_id*
   GET
   UPDATE
   DELETE

  * /api/route/
   GET
   POST

  * /api/route/*competitor_id*
   GET
   UPDATE
   DELETE
