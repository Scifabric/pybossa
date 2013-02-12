
.. _api:

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
    
For example, you can get a list of registered applications like this::

    GET http://{pybossa-site-url}/api/app

Or a list of Tasks::

    GET http://{pybossa-site-url}/api/task

For a list of TaskRuns use::

    GET http://{pybossa-site-url}/api/taskrun

.. note::
    By default PyBossa limits the list of items to 20. If you want to get more
    items, use the keyword **limit=N** with **N** being a number to get that
    amount.

.. note::
    You can use the keyword **offset=N** in any **GET** query to skip that many 
    rows before beginning to get rows. If both **offset** and **limit** appear, 
    then **offset** rows are skipped before starting to count the **limit** rows 
    that are returned.

Get
~~~

Get a specific domain object by id (by default any GET action will return only
20 objects, you can get more or less objects using the **limit** option).
Returns domain object.::

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

.. note::
    By default all GET queries return a maximum of 20 objects unless the
    **limit** keyword is used to get more: limit=50

Create
~~~~~~

Create a domain object. Returns created domain object.::

    POST http://{pybossa-site-url}/api/{domain-object}[?api_key=API-KEY]

.. note::
    Some POST actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Update
~~~~~~

Update a domain object::

  PUT http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some PUT actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Delete
~~~~~~

Delete a domain object::

  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some DELETE actions may require to authenticate & authorize the request. Use the
    ?api_key arguement to pass the **API-KEY**.

Requesting a new task for current user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can request a new task for the current user (anonymous or authenticated)
by::

    GET http://{pybossa-site-url}/api/{app.id}/newtask

This will return a domain Task object in JSON format if there is a task
available for the user, otherwise it will return **None**.

.. note::
    Some applications will want to pre-load the next task for the current user.
    This is possible by passing the argument **?offset=1** to the **newtask**
    endpoint.

Example Usage
-------------

Create an Application object::

  curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myapp", "info":{"xyz":1}}' 'http://localhost:5000/api/app?api_key=API-KEY'
