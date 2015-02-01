django-seuranta
===============

An application dedicated to live gps tracking for orienteering events.
You can either use django-seuranta as standalone application or add it to
your django project.


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
   params:
    - username
    - password

  * /api/auth_token/destroy
   POST -- Void user authorization token
   params:
    - username
    - password

  * /api/competition
   GET
   POST

  * /api/competition/<competition_id>
   GET
   UPDATE
   DESTROY

  * /api/map/<competition_id>[.jpg]
   GET
   UPDATE

  * /api/competitor
   GET
   POST

  * /api/competitor/<competitor_id>
   GET
   UPDATE
   DESTROY

  * /api/route/
   GET
   POST

  * /api/route/<competitor_id>
   GET
   UPDATE
   DESTROY
