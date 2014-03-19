==================
django-seuranta
==================

An application dedicated to live gps tracking for orienteering purposes.

Prerequisites
-------------

django-seuranta requires:

django
django-timezone-field

.. include:: ../README.rst

Installation
------------

1. Add ``"seuranta"`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # …
        "seuranta",
    )


2. Include the seuranta URLconf in your project urls.py like this::

    url(r'^seuranta/', include('seuranta.urls')),

3. Run `python manage.py migrate` to create the seuranta models.


Usage
-----

To be completed

Settings
--------

At the moment there are no settings


License
-------

`MIT`_

.. _jQuery: http://jquery.com/
.. _LeafletJS: http://leafletjs.com/
.. _RaphaelJS: http://raphaeljs.com/
.. _MIT: http://rphlo.mit-license.org/
