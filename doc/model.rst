====================
Domain Model and API
====================

This section introduces the main domain objects present in the BOSSA system and how they can be accessed via the API.

Domain Model
============

Overview
--------

BOSSA has 4 main domain objects:

  * App: the overall Application/Project to which Tasks are associated.

    * HasMany: Tasks

  * Task: an individual Task which can be performed by a user. A Task is associated to an App.

    * HasA: App
    * HasMany: TaskRuns

  * TaskRun: the results of a specific User performing a specific task

    * HasA: Task
    * HasA: User

  * User: a user account

There are some attributes common across most of the domain objects notably:

  * `create_time`: the Datetime (as an integer) when object was created.
  * `info`: a 'blob-style' attribute into which one can store arbitrary JSON. This attribute is use to any additional information one wants (e.g. Task configuration or Task results on TaskRun)

The following excerpts directly from the PyBossa source to provide
documentation of main model attributes.

App
---

.. autoclass:: pybossa.model.App
   :members:

Task
----

.. autoclass:: pybossa.model.Task
   :members:

TaskRun
-------

.. autoclass:: pybossa.model.TaskRun
   :members:


RESTful API
===========

The RESTful API is located at::

  http://{pybossa-site-url}/api

It expects and returns JSON.

.. autoclass:: pybossa.api.APIBase
   :members:

Operations
----------

The following operations are supported:

List
~~~~

List domain objects::
     
    GET http://{pybossa-site-url}/api/{domain-object}

Get
~~~

Get a specific domain object by id. Returns domain object.::

    GET http://{pybossa-site-url}/api/{domain-object}/{id}

Create
~~~~~~

Create a domain object. Returns created domain object.::

    POST http://{pybossa-site-url}/api/{domain-object}

Update
~~~~~~

Update a domain object (not yet implemented)::

  PUT http://{pybossa-site-url}/api/{domain-object}/{id}

Delete
~~~~~~

Delete a domain object (not yet implemented)::

  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}


Example Usage
-------------

Create an Application object::

  curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myapp", "info":{"xyz":1}}' 'http://localhost:5000/api/app'


