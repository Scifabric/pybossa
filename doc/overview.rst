================
PyBossa Overview
================

The following diagram gives an overview of how a (Py)Bossa system functions:

.. image:: https://docs.google.com/drawings/pub?id=1ZXoCX5Q5AbOXu7-99yrNPoNLCpdxzONsXpCXEL6-4_Q&w=960&h=720
   :align: center
   :alt: PyBossa Architecture
   :width: 100%

PyBossa itself implements the section marked 'Bossa Core' and provides a
platform on which Tasks can be created by Task Creators and from which Tasks
can be accessed by Task Presenters (and on which certain types of Task
Presenters can directly run). Full documentation of the API provided by PyBossa
and which Task Creator and Task Presenters can use is to be found in
:doc:`model`.


Task Creators
=============

Task Creators are responsible for the creation of Tasks (and related entites --
Apps, etc) in PyBossa. As such they will usually operate entirely
outside of PyBossa itself interacting with PyBossa via the API.

*Coming soon*: A demonstration python script for creating tasks from a CSV file
(creatable from any spreadsheet programme such as Excel or Google Spreadsheets)
can be found in the contrib directory of the PyBossa source.


Task Presenters
===============

Task presenters are responsible for presenting tasks to user in an appropriate
user interface. For example, if a task involves classifying an image then a
Task Presenter could be an html page into which the image has been inserted
along with a form where the user can submit the response (the Task Presenter
would also take care of submitting that response back to the PyBossa server via
an API call).

Task Presenters can be written in any language and run anywhere as long as they
can communicate with the PyBossa server via its API.

However, Task Presenters that wish to run as part of a PyBossa instance must be
written in HTML and javascript. In addition, Task Presenters running on as part
of a PyBossa instance will have available some additional information such as
the id of the current logged in user performing the task.


BOSSA Original Architecture
===========================

PyBossa derives from the original BOSSA_ implementation. The following are some
useful references to that original implementation:

* http://boinc.berkeley.edu/trac/wiki/BossaImplementation
* BOSSA Reference: http://boinc.berkeley.edu/trac/wiki/BossaReference

.. _BOSSA: http://bossa.berkeley.edu/

