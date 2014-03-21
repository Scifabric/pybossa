
.. _api:

RESTful API
===========

The RESTful API is located at::

  http://{pybossa-site-url}/api

It expects and returns JSON.

.. autoclass:: pybossa.api.api_base.APIBase
   :members:

.. autoclass:: pybossa.api.AppAPI
   :members:

.. autoclass:: pybossa.api.TaskAPI
   :members:

.. autoclass:: pybossa.api.TaskRunAPI
   :members:

.. autoclass:: pybossa.api.CategoryAPI
   :members:

.. autoclass:: pybossa.api.GlobalStatsAPI
   :members:

.. autoclass:: pybossa.api.VmcpAPI
   :members:

Some requests will need an **API-KEY** to authenticate & authorize the
operation. You can get your API-KEY in your *profile* account.

The returned objects will have a **links** and **link** fields, not included in
the model in order to support `Hypermedia as the Engine of Application State`_
(also known as HATEOAS), so you can know which are the relations between
objects.

All objects will return a field **link** which will be the absolute URL for
that specific object within the API. If the object has some parents, you will
find the relations in the **links** list. For example, for a Task Run you will
get something like this:

.. code-block:: javascript

    {
    "info": 65,
    "user_id": null,
    "links": [
        "<link rel='parent' title='app' href='http://localhost:5000/api/app/90'/>",
        "<link rel='parent' title='task' href='http://localhost:5000/api/task/5894'/>"
    ],
    "task_id": 5894,
    "created": "2012-07-07T17:23:45.714184",
    "finish_time": "2012-07-07T17:23:45.714210",
    "calibration": null,
    "app_id": 90,
    "user_ip": "X.X.X.X",
    "link": "<link rel='self' title='taskrun' href='http://localhost:5000/api/taskrun/8969'/>",
    "timeout": null,
    "id": 8969
    }

The object link will have a tag **rel** equal to **self**, while the parent
objects will be tagged with **parent**. The **title** field is used to specify
the type of the object: task, taskrun or app.

Apps will not have a **links** field, because these objects do not have
parents.

Tasks will have only one parent: the associated application.

Task Runs will have only two parents: the associated task and associated app.

.. _`Hypermedia as the Engine of Application State`: http://en.wikipedia.org/wiki/HATEOAS 


.. _rate-limiting:

Rate Limiting
-------------

Rate Limiting in PyBossa v2.0.1 has been enabled for all the API endpoints.
The rate limiting gives any user, using the IP, **a window of 15 minutes to do at
most 300 requests per endpoint**.

This new feature includes in the headers the following values to throttle your
requests without problems:

* **X-Rate-Limit-Limit**: the rate limit ceiling for that given request
* **X-Rate-Limit-Remaining**: the number of requests left for the 15 minute window
* **X-Rate-Limit-Reset**: the remaining window before the rate limit resets in UTC epoch seconds

We recommend to use the Python package **requests** for interacting with
PyBossa, as it is really simple to check those values:

.. code-block:: python

    import requests
    import time

    res = requests.get('http://SERVER/api/app')
    if int(res.headers['X-Rate-Limit-Remaining']) < 10:
        time.sleep(300) # Sleep for 5 minutes
    else:
        pass # Do your stuff




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

Finally, you can get a list of users by doing::

    GET http://{pybossa-site-url}/api/user

.. note::
    Please, notice that in order to keep users privacy, only their locale and
    nickname will be shared by default. Optionally, users can disable privacy
    mode in their settings. By doing so, also their fullname and account
    creation date will be visible for everyone through the API.

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
    ?api_key argument to pass the **API-KEY**.

If the object is not found you will get a JSON object like this:

.. code-block:: JavaScript

    {
        "status": "failed",
        "action": "GET",
        "target": "app",
        "exception_msg": "404 Not Found",
        "status_code": 404,
        "exception_cls": "NotFound"
    }

Any other error will return the same object but with the proper status code and
error message.

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

.. note::
    If the search does not find anything, the server will return an empty JSON
    list []

Create
~~~~~~

Create a domain object. Returns created domain object.::

    POST http://{pybossa-site-url}/api/{domain-object}[?api_key=API-KEY]

.. note::
    Some POST actions may require to authenticate & authorize the request. Use the
    ?api_key argument to pass the **API-KEY**.

If an error occurs, the action will return a JSON object like this:

.. code-block:: JavaScript

    {
        "status": "failed",
        "action": "POST",
        "target": "app",
        "exception_msg": "type object 'App' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to an App, Task or TaskRun object.

Update
~~~~~~

Update a domain object::

  PUT http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some PUT actions may require to authenticate & authorize the request. Use the
    ?api_key argument to pass the **API-KEY**.

If an error occurs, the action will return a JSON object like this:

.. code-block:: JavaScript

    {
        "status": "failed",
        "action": "PUT",
        "target": "app",
        "exception_msg": "type object 'App' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to an App, Task or TaskRun object.

Delete
~~~~~~

Delete a domain object::

  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some DELETE actions may require to authenticate & authorize the request. Use the
    ?api_key argument to pass the **API-KEY**.

If an error occurs, the action will return a JSON object like this:

.. code-block:: JavaScript

    {
        "status": "failed",
        "action": "DELETE",
        "target": "app",
        "exception_msg": "type object 'App' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to an App, Task or TaskRun object.


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


Requesting the user's oAuth tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user who has registered or signed in with any of the third parties supported
by PyBossa (currently Twitter, Facebook and Google) can request his own oAuth
tokens by doing::

    GET http://{pybossa-site-url}/api/{app.id}/token

Additionally, the user can specify any of the tokens if only its retrieval is
desired::

    GET http://{pybossa-site-url}/api/{app.id}/token/{provider}

Where 'provider' will be any of the third parties supported, i.e. 'twitter',
'facebook' or 'google'.

Example Usage
-------------

Create an Application object::

  curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myapp", "info":{"xyz":1}}' 'http://localhost:5000/api/app?api_key=API-KEY'
