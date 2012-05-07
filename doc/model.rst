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

Some requests will need an **API-KEY** to authenticate & authorize the
operation. You can get your API-KEY in your *profile* account.

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

    GET http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some GET actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Search
~~~~~~

Get a list of domain objects by its fields. Returns a list of domain objects
matching the query::

    GET http://{pybossa-site-url}/api/{domain-object}[?domain-object-field=value]

Multiple fields can be used separated by the **&** symbol::

    GET http://{pybossa-site-url}/api/{domain-object}[?field1=value&field2=value2]

It is possible to limit the number of returned objects::

    GET http://{pybossa-site-url}/api/{domain-object}[?field1=value&limit=20]


Create
~~~~~~

Create a domain object. Returns created domain object.::

    POST http://{pybossa-site-url}/api/{domain-object}[?api_key=API-KEY]

.. note::
    Some POST actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Update
~~~~~~

Update a domain object (not yet implemented)::

  PUT http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some PUT actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Delete
~~~~~~

Delete a domain object (not yet implemented)::

  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some DELETE actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Example Usage
-------------

Create an Application object::

  curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myapp", "info":{"xyz":1}}' 'http://localhost:5000/api/app?api_key=API-KEY'


