
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

.. autoclass:: pybossa.api.ProjectAPI
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
        "<link rel='parent' title='project' href='http://localhost:5000/api/project/90'/>",
        "<link rel='parent' title='task' href='http://localhost:5000/api/task/5894'/>"
    ],
    "task_id": 5894,
    "created": "2012-07-07T17:23:45.714184",
    "finish_time": "2012-07-07T17:23:45.714210",
    "calibration": null,
    "project_id": 90,
    "user_ip": "X.X.X.X",
    "link": "<link rel='self' title='taskrun' href='http://localhost:5000/api/taskrun/8969'/>",
    "timeout": null,
    "id": 8969
    }

The object link will have a tag **rel** equal to **self**, while the parent
objects will be tagged with **parent**. The **title** field is used to specify
the type of the object: task, taskrun or project.

Projects will not have a **links** field, because these objects do not have
parents.

Tasks will have only one parent: the associated project.

Task Runs will have only two parents: the associated task and associated project.

.. _`Hypermedia as the Engine of Application State`: http://en.wikipedia.org/wiki/HATEOAS 


.. _rate-limiting:

Rate Limiting
-------------

Rate Limiting has been enabled for all the API endpoints (since PyBossa v2.0.1).
The rate limiting gives any user, using the IP, **a window of 15 minutes to do at
most 300 requests per endpoint**.

This new feature includes in the headers the following values to throttle your
requests without problems:

* **X-RateLimit-Limit**: the rate limit ceiling for that given request
* **X-RateLimit-Remaining**: the number of requests left for the 15 minute window
* **X-RateLimit-Reset**: the remaining window before the rate limit resets in UTC epoch seconds

We recommend to use the Python package **requests** for interacting with
PyBossa, as it is really simple to check those values:

.. code-block:: python

    import requests
    import time

    res = requests.get('http://SERVER/api/project')
    if int(res.headers['X-RateLimit-Remaining']) < 10:
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


The API is context aware in the sense that if you've an API-KEY and you're authenticating
the calls, then, the server will send you first your own related data: projects, tasks, and
task runs. You can get access to all the projects, tasks, and task runs (the whole data base) using the
parameter: **all=1**.

For example, if an anonymous user access the generic api endpoints like::

    GET http://{pybossa-site-url}/api/project

It will return all the projects from the DB, ordering them by ID. If you access it
like authenticating yourself:: 

    GET http://{pybossa-site-url}/api/project?api_key=YOURKEY

Then, you will get your own list of projects. In other words, the projects that you 
own. If you don't have a project, but you want to explore the API then you can use
the **all=1** argument::

    GET http://{pybossa-site-url}/api/project?api_key=YOURKEY&all=1

This call will return all the projects from the DB ordering by ID.

For example, you can get a list of your Projects like this::

    GET http://{pybossa-site-url}/api/project
    GET http://{pybossa-site-url}/api/project?api_key=YOURKEY
    GET http://{pybossa-site-url}/api/project?api_key=YOURKEY&all=1

Or a list of available Categories:: 

    GET http://{pybossa-site-url}/api/category

Or a list of Tasks::

    GET http://{pybossa-site-url}/api/task
    GET http://{pybossa-site-url}/api/task?api_key=YOURKEY
    GET http://{pybossa-site-url}/api/task?api_key=YOURKEY&all=1

For a list of TaskRuns use::

    GET http://{pybossa-site-url}/api/taskrun
    GET http://{pybossa-site-url}/api/taskrun?api_key=YOURKEY
    GET http://{pybossa-site-url}/api/taskrun?api_key=YOURKEY&all=1

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
    amount. There is a maximum of 100 to the **limit** keyword, so if you try to
    get more items at once it won't work.

.. note::
    **DEPRECATED (see next Note for a better and faster solution)**
    You can use the keyword **offset=N** in any **GET** query to skip that many 
    rows before beginning to get rows. If both **offset** and **limit** appear, 
    then **offset** rows are skipped before starting to count the **limit** rows 
    that are returned.

.. note::
    You can paginate the results of any GET query using the last ID of the
    domain object that you have received and the parameter: **last_id**. For 
    example, to get the next 20 items
    after the last project ID that you've received you will write the query
    like this: GET /api/project?last_id={{last_id}}.

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

.. code-block:: js

    {
        "status": "failed",
        "action": "GET",
        "target": "project",
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


It is possible to access first level JSON keys within the **info** field of Projects,
Tasks, Task Runs and Results::

    GET http://{pybossa-site-url}/api/{domain-object}[?field1=value&info=foo::bar&limit=20]

To search within the first level (nested keys are not supported), you have to use the
following format::

    info=key::value

For adding more keys::

    info=key1::value1|key2::value2|keyN::valueN

These parameters will be ANDs, so, it will return objects that have those keys with 
and **and** operator.

It is also possible to use full text search queries within those first level keys. For
searching like that all you have to do is adding the following argument::

    info=key1::value1&fulltextsearch=1

That will return every object in the DB that has a key equal to key1 and contains in
the value the word value1.

Another option could be the following::

    info=key1::value1|key2:word1%26word2&fulltextsearch=1

This second query will return objects that has the words word1 and word2. It's important
to escape the & operator with %26 to use the and operator.

.. note::
    By default all GET queries return a maximum of 20 objects unless the
    **limit** keyword is used to get more: limit=50. However, a maximum amount
    of 100 objects can be retrieved at once.

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

.. code-block:: js

    {
        "status": "failed",
        "action": "POST",
        "target": "project",
        "exception_msg": "type object 'Project' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to a Project, Task or TaskRun object.

Update
~~~~~~

Update a domain object::

  PUT http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some PUT actions may require to authenticate & authorize the request. Use the
    ?api_key argument to pass the **API-KEY**.

If an error occurs, the action will return a JSON object like this:

.. code-block:: js

    {
        "status": "failed",
        "action": "PUT",
        "target": "project",
        "exception_msg": "type object 'Project' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to a project, Task or TaskRun object.

Delete
~~~~~~

Delete a domain object::

  DELETE http://{pybossa-site-url}/api/{domain-object}/{id}[?api_key=API-KEY]

.. note::
    Some DELETE actions may require to authenticate & authorize the request. Use the
    ?api_key argument to pass the **API-KEY**.

If an error occurs, the action will return a JSON object like this:

.. code-block:: js

    {
        "status": "failed",
        "action": "DELETE",
        "target": "project",
        "exception_msg": "type object 'Project' has no attribute 'short_ame'",
        "status_code": 415,
        "exception_cls": "AttributeError"
    }

Where **target** will refer to a Project, Task or TaskRun object.


Requesting a new task for current user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can request a new task for the current user (anonymous or authenticated)
by::

    GET http://{pybossa-site-url}/api/{project.id}/newtask

This will return a domain Task object in JSON format if there is a task
available for the user, otherwise it will return **None**.

.. note::
    Some projects will want to pre-load the next task for the current user.
    This is possible by passing the argument **?offset=1** to the **newtask**
    endpoint.


Requesting the user's oAuth tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user who has registered or signed in with any of the third parties supported
by PyBossa (currently Twitter, Facebook and Google) can request his own oAuth
tokens by doing::

    GET http://{pybossa-site-url}/api/token?api_key=API-KEY

Additionally, the user can specify any of the tokens if only its retrieval is
desired::

    GET http://{pybossa-site-url}/api/token/{provider}?api_key=API-KEY

Where 'provider' will be any of the third parties supported, i.e. 'twitter',
'facebook' or 'google'.

Example Usage
-------------

Create a Project object:

.. code-block:: bash

    curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myproject", "info":{"xyz":1}}' 'http://localhost:5000/api/project?api_key=API-KEY'
