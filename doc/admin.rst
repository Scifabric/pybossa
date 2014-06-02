======================
Administrating PyBossa
======================

PyBossa has three type of users: anonymous, authenticated and administrators.
By default the first created user in a PyBossa server will become an
administrator and manage the site with full privileges.

And admin user will be able to access the admin page by clicking in the user
name and then in the link *Admin site*.

.. image:: http://i.imgur.com/Xm6c42x.png

Administrators can manage three different areas of the server:

 1. Featured projects
 2. Categories, and
 3. Administrators

.. image:: http://i.imgur.com/rhGXkO4.png
    :width:100%

.. note::
    Admins can also modify all projects, and also see which projects are marked
    as **Draft**: projects that do not have at least one task and
    a :ref:`task-presenter` to allow other volunteers to participate.

.. note::
    A fourth option is available on the Admin Site menu. Here, admins will be able
    to obtain a list of all registered users in the PyBossa system, in either
    json or csv formats.


.. _featured-apps:

Featured Projects
=================

In this section, admins can add/remove projects to the front page of the
site. 

.. image:: http://i.imgur.com/Jpr3bGh.png
    :width:100%

Basically, you will see a green button to add a project to the Featured
selection, or a red one to remove it from the front page.


.. _categories:

Categories
==========

PyBossa provides by default two type of categories:

1. **Thinking**: for projects where the users can use their skills to solve
   a problem (i.e. image or sound pattern recognition).
2. **Sensing**: for projects where the users can help gathering data using
   tools like EpiCollect_ and then analyze the data in the PyBossa server.

Admins can add as many categories as they want, just type then and its
description and click in the green button labeled: Add category.

.. _EpiCollect: http://plus.epicollect.net

.. image:: http://i.imgur.com/otR6wcG.png
    :width: 100%

.. note::
    You cannot delete a category if it has one or more projects associated
    with it. You can however rename the category or delete it when all the
    associated projects are not linked to the given category.


.. _administrators:

Administrators
==============

In this section an administrator will be able to add/remove users to the admin
role. Basically, you can search by user name -nick name- and add them to the
admin group.

.. image:: http://i.imgur.com/IdDKo8P.png
    :width:100%

As with the :ref:`categories` section, a green button will allow you to add the user
to the admin group, while a red button will be shown to remove the user from
the admin group.



