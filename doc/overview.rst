================
PyBossa Overview
================

PyBossa is an open source platform that allows you to create web microtasking
applications where volunteers could participate using their own web browsers.

PyBossa has two main components:

* the server and
* the applications.

.. note:: 

    PyBossa provides a :doc:`api` that will give you access to some of the
    :doc:`model` objects.

The server
==========

The PyBossa server is a Python_ web application that manages **tasks** for web
applications delivering them to users using a simple :doc:`api`.

The `Citizen Cyberscience Centre`_ and the `Open Knowledge Foundation`_ provide
the server CrowdCrafting.org_ so if you want, you can start directly using this
service without any cost, or if you prefer :doc:`installing_pybossa` yourself.

.. _Python: http://python.org
.. _`Citizen Cyberscience Centre`: http://citizencyberscience.net
.. _`Open Knowledge Foundation`: http://okfn.org
.. _`CrowdCrafting.org`: http://crowdcrafting.org

Architecture
~~~~~~~~~~~~
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
:doc:`api`.


The Applications
================
A PyBossa application is an HTML page with some JavaScript_ that will load
a **task** from a PyBossa server and present it to the volunteer and ask the 
user to, for instance, classify an image, transcribe a hand written document, etc.

A PyBossa application has two main components:

* A **Task Presenter**: an HTML document where the JavaScript_ will load the
  task data into the DOM_ (see :ref:`task-creator`); and 

* A **Task Creator**: usually a script that will upload the tasks for the
  application into the PyBossa server (see :ref:`task-presenter`).

Applications can be easily created using two approaches:

* **Using the Web interface**: where you can create an application, write the 
  *Task Presenter*  and upload the tasks using the *simplified built-in 
  Task Creator* (you can upload a CSV file or use a Google Docs Spreadsheet 
  link exported as CSV); or 
* **Using the** :doc:`api`: where you will be able to create the application, 
  write the *Task Presenter* and *Task Creator* using your preferred text
  editor locally in your computer.

The **Web Interface** is a nice start point to learn a bit more about the
PyBossa architecture and how you can develop a *simple* application in a really
short time, while the :doc:`api` will give you more options in terms of
flexibility at the cost of writing your own *Task Creator*.

.. note::

    It is possible to create the application using the web interface, and then
    work locally in your computer developing the Task Presenter and Creator.

.. _Javascript: http://en.wikipedia.org/wiki/JavaScript
.. _DOM: http://en.wikipedia.org/wiki/Document_Object_Model


.. _task-creator:

Task Creator
~~~~~~~~~~~~

Task Creators are responsible for the creation of Tasks (and related entites --
Apps, etc) in PyBossa. As such they will usually operate entirely
outside of PyBossa itself interacting with PyBossa via the API.

The PyBossa project provides several PyBossa application templates that can be
re-used for creating a new application really easily:

* `Flickr Person Finder`_: an image classification template,
* `Urban Parks`_: a geo-localizing using web-maps template,
* `PDF Transcribe`_: a trancription template.

.. _`Flickr Person Finder`: https://github.com/PyBossa/app-flickrperson
.. _`Urban Parks`: https://github.com/PyBossa/app-geocoding
.. _`PDF Transcribe`: https://github.com/PyBossa/pdftranscribe

The template applications provide the:

* **Task Creator**: check in the repository the *createTasks.py* script,
* **Task Presenter**: check in the repository the *template.html* file,
* **Tutorial**: check in the repository the *tutorial.html* file,
* **Application description**: check in the repository the **app.json**
  and **long_description.html** files.


We recommend you to read the :doc:`user/tutorial` as it gives *a step by step*
guide about how you can create an application, write the Task Creator and
Presenter from scratch using the `Flickr
Person Finder`_ template application.

.. _task-presenter:

Task Presenter
~~~~~~~~~~~~~~

Task presenters are responsible for presenting tasks to user in an appropriate
user interface. For example, if a task involves classifying an image then a
Task Presenter could be an html page into which the image has been inserted
along with a form where the user can submit the response (the Task Presenter
would also take care of submitting that response back to the PyBossa server via
an API call).

Task Presenters can be written in any language and run anywhere as long as they
can communicate with the PyBossa server via its API.

However, Task Presenters that wish to run as part of a PyBossa instance must be
written in HTML and JavaScript. In addition, Task Presenters running on as part
of a PyBossa instance will have available some additional information such as
the id of the current logged in user performing the task.

The PyBossa framework provides several template applications that can be
re-used to create your own application:

* `Flickr Person Finder`_: an image classification template,
* `Urban Parks`_: a geo-localizing using web-maps template,
* `PDF Transcribe`_: a trancription template.

The template applications provide the:

* **Task Creator**: check in the repository the *createTasks.py* script,
* **Task Presenter**: check in the repository the *template.html* file,
* **Tutorial**: check in the repository the *tutorial.html* file,
* **Application description**: check in the repository the **app.json**
  and **long_description.html** files.

We recommend you to read the :doc:`user/tutorial` as it gives *a step by step*
guide about how you can create an application, write the Task Creator and
Presenter from scratch using the `Flickr
Person Finder`_ template application.


BOSSA Original Architecture
===========================

PyBossa derives from the original BOSSA_ implementation. The following are some
useful references to that original implementation:

* http://boinc.berkeley.edu/trac/wiki/BossaImplementation
* BOSSA Reference: http://boinc.berkeley.edu/trac/wiki/BossaReference

.. _BOSSA: http://bossa.berkeley.edu/

