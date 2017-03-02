django-seuranta
===============

Live gps tracking server for orienteering events.

[![Build Status](https://travis-ci.org/rphlo/django-seuranta.svg?branch=master)](https://travis-ci.org/rphlo/django-seuranta)
[![Coverage Status](https://coveralls.io/repos/rphlo/django-seuranta/badge.svg?branch=dev)](https://coveralls.io/r/rphlo/django-seuranta?branch=dev)


Requirement
-----------

Python version 2.7


Installation
------------

run ```./install.sh``` It will ask for a username and a password for a super user. that you can use to login in the admin.
once installed you can run the server with ```python manage.py runserver``` admin is available at ```http://127.0.0.1:8000/admin/``` see next paragraph for API endpoints


API Endpoints
-------------

Note: API is browsable and endpoints are documented on their own page.
  
  * /api/time

    GET -- Return Server Unix Time

  * /api/auth_token/obtain
   
    POST -- Return user authorization token

    parameters:
      - username
      - password


  * /api/auth_token/destroy
  
    POST -- Void user authorization token

    parameters
    - username
    - password


  * /api/competitor_token/obtain
  
    POST -- Return competitor publishing token
  
    parameters:
    - competitor
    - access_code


  * /api/competitor_token/destroy
   
    POST -- Void competitor publishing token
    
    parameters:
    - competitor
    - access_code


  * /api/competition
   
    GET -- List competitions
    

    POST -- Create a competition (requires an user account)

  * /api/competition/*competition_id*
   
    GET -- Retrieve a competition

    PUT/PATCH -- Update competition data (available to competition publisher)

    DELETE -- Delete a competition (available to competition publisher)

  * /api/map/*competition_id*[.jpg]

    GET -- Retrieve info about competition Map

    PUT/PATCH -- Update info about competition map (available to competition publisher)

  * /api/competitor

    GET -- List competitors
 
    POST -- Create a competitor (Success depends on competition signup policy)

  * /api/competitor/*competitor_id*

    GET -- Retrieve competitor info

    PUT/PATCH -- Update competitor info (may require a competitor publishing token)

    DELETE -- Delete a competitor (competition publisher only)

  * /api/route/

    GET -- Retrieve posted route data (special encoding)

    POST -- Post route data (special encoding)

  * /api/route/*competitor_id*

    GET -- Retrieve a the full route for a competitor

    PUT/PATCH -- Update the full route for a competitor
