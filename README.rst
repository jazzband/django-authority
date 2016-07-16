================
django-authority
================

.. image:: https://jazzband.co/static/img/badge.svg
   :target: https://jazzband.co/
   :alt: Jazzband

.. image:: https://travis-ci.org/jazzband/django-authority.svg?branch=master
    :target: https://travis-ci.org/jazzband/django-authority

.. image:: https://codecov.io/gh/jazzband/django-authority/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/jazzband/django-authority

This is a Django app for per-object-permissions that includes a bunch of
helpers to create custom permission checks.

The main website for django-authority is
`django-authority.readthedocs.org`_. You can also install the
`in-development version`_ of django-authority with
``pip install django-authority==dev`` or ``easy_install django-authority==dev``.

.. _`django-authority.readthedocs.org`: https://django-authority.readthedocs.io/
.. _in-development version: https://github.com/jazzband/django-authority/archive/master.zip#egg=django-authority-dev

Example
=======

To get the example project running do:

- Bootstrap the environment by running in a virtualenv::

    pip install Django
    pip install -e .

- Sync the database::

    python example/manage.py migrate

- Run the development server and visit the admin at http://127.0.0.1:8000/admin/::

    python example/manage.py runserver

Now create a flatage and open it to see some of the templatetags in action.
Don't hesitate to use the admin to edit the permission objects.

Please use https://github.com/jazzband/django-authority/issues/ for issues and bug reports.

Documentation
=============

The documenation is currently in development. You can create a nice looking
html version using the setup.py::

    python setup.py build_sphinx

Changelog:
==========

0.11 (2016-07-17):
-----------------

* Added Migration in order to support Django 1.8

* Dropped Support for Django 1.7 and lower

* Remove SQL Migration Files

* Documentation Updates

* Fix linter issues

0.10 (2015-12-14):
------------------

* Fixed a bug with BasePermissionForm and django 1.8

0.9 (2015-11-11):
-----------------

* Added support for Django 1.7 and 1.8

* Dropped support for Django 1.3

0.8 (2013-12-20):
-----------------

* Added support for Django 1.6

0.7 (2013-07-03):
-----------------

* No longer doing dependent sub-queries. It will be faster to do two small
  queries instead of one with a dependent sub-query in the general case.

0.6 (2013-06-13):
-----------------

* Added support for custom user models (Django 1.5 only).

0.5 (2013-03-18):
-----------------

* It is now possible to minimize the number of queries when using
  django-authority by caching the results of the Permission query. This can be
  done by adding ``AUTHORITY_USE_SMART_CACHE = True`` to your settings.py
* Confirmed support (via travis ci) for all combinations of Python 2.6,
  Python2.7 and Django 1.3, Django 1.4, Django 1.5. Added Python 3.3 support
  for Django 1.5


0.4 (2010-01-15):
-----------------

* Fixed an issue with the UserPermissionForm not being able to override the
  widget of the user field.

* Added ability to override form class in ``add_permission`` view.

* Added easy way to assign permissions via a permission instance, e.g.::

    from django.contrib.auth.models import User
    from mysite.articles.permissions import ArticlePermission

    bob = User.objects.get(username='bob')
    article_permission = ArticlePermission(bob)
    article_permission.assign(content_object=article)


0.3 (2009-07-28):
-----------------

* This version adds multiple fields to the Permission model and is
  therefore a **backwards incompatible** update.

  This was required to add a feature that allows users to request,
  withdraw, deny and approve permissions. Request and approval date
  are now saved, as well as an ``approved`` property. An admin action has
  been added for bulk approval.

  To migrate your existing data you can use the SQL files included in
  the source (`migrations/`_), currently available for MySQL, Postgres
  and SQLite.

* The templatetags have also been refactored to be easier to customize
  which required a change in the template tag signature:

  Old::

    {% permission_form flatpage %}
    {% permission_form flatpage "flatpage_permission.top_secret" %}
    {% permission_form OBJ PERMISSION_LABEL.CHECK_NAME %}

  New::

    {% permission_form for flatpage %}
    {% permission_form for flatpage using "flatpage_permission.top_secret" %}
    {% permission_form for OBJ using PERMISSION_LABEL.CHECK_NAME [with TEMPLATE] %}

  New templatetags:

  * ``permission_request_form``
  * ``get_permission_request``
  * ``get_permission_requests``
  * ``permission_request_approve_link``
  * ``permission_request_delete_link``
  * ``request_url_for_obj``

* The ``add_permission`` view is now accessible with GET requests and
  allows to request permissions, but also add them (only for users with
  the 'authority.add_permission' Django permission).

.. _`migrations/`: https://github.com/jazzbands/django-authority/tree/master/migrations
