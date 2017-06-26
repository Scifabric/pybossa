
.. _api:

RESTful API
===========

The RESTful API is located at::

  http://{pybossa-site-url}/api

It expects and returns JSON.

.. autoclass:: pybossa.api.api_base.APIBase
   :members:

.. autoclass:: pybossa.api.UserAPI
   :members:

.. autoclass:: pybossa.api.ProjectAPI
   :members:

.. autoclass:: pybossa.api.BlogpostAPI
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

.. autoclass:: pybossa.api.FavoritesAPI
   :members:

.. autoclass:: pybossa.api.HelpingMaterial
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

Rate Limiting has been enabled for all the API endpoints (since PYBOSSA v2.0.1).
The rate limiting gives any user, using the IP, **a window of 15 minutes to do at
most 300 requests per endpoint**.

This new feature includes in the headers the following values to throttle your
requests without problems:

* **X-RateLimit-Limit**: the rate limit ceiling for that given request
* **X-RateLimit-Remaining**: the number of requests left for the 15 minute window
* **X-RateLimit-Reset**: the remaining window before the rate limit resets in UTC epoch seconds

We recommend to use the Python package **requests** for interacting with
PYBOSSA, as it is really simple to check those values:

.. code-block:: python

    import requests
    import time

    res = requests.get('http://SERVER/api/project')
    if int(res.headers['X-RateLimit-Remaining']) < 10:
        time.sleep(300) # Sleep for 5 minutes
    else:
        pass # Do your stuff


List
----

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

Order by
--------

Any query can be ordered by an attribute of the domain object that you are querying. For example
you can get a list of tasks ordered by ID::

    GET http://{pybossa-site-url}/api/task?orderby=id

If you want, you can order them in descending order::

    GET http://{pybossa-site-url}/api/task?orderby=id&desc=true


Check all the attritbutes that you can use to order by in the `Domain Object section <http://docs.pybossa.com/en/latest/model.html>`_.

.. note::
    Please, notice that in order to keep users privacy, only their locale and
    nickname will be shared by default. Optionally, users can disable privacy
    mode in their settings. By doing so, also their fullname and account
    creation date will be visible for everyone through the API.

.. note::
    By default PYBOSSA limits the list of items to 20. If you want to get more
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

Related data
~~~~~~~~~~~~

For Tasks, TaskRuns and Results you can get the associated data using the argument: *related=True*.

This flag will allow you to get in one call all the TaskRuns and Result for a given task. You can do the same for a TaskRun getting the Task and associated Result, and for a Result getting all the task_runs and associated Task.

Projects do not have this feature, as it will be too expensive for the API.

Get
---

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
------

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

Full text search
----------------

It is also possible to use full text search queries within those first level keys (as seen before). For searching like that all you have to do is adding the following argument::

    info=key1::value1&fulltextsearch=1

That will return every object in the DB that has a key equal to key1 and contains in
the value the word value1.

Another option could be the following::

    info=key1::value1|key2:word1%26word2&fulltextsearch=1

This second query will return objects that has the words word1 and word2. It's important
to escape the & operator with %26 to use the and operator.

When you use the fulltextsearch argument, the API will return the objects enriched with the following two fields:

 * **headline**: The matched words of the key1::value1 found, with <b></b> items to highlight them.
 * **rank**: The ranking returned by the database. Ranking attempts to measure how relevant documents are to a particular query, so that when there are many matches the most relevant ones can be shown first.

Here you have an example of the expected output for an api call like this:: 

    /api/task?project_id=1&info=name::ipsum%26bravo&fulltextsearch=1 

.. code-block:: python

    [
      {
        "info": {
          "url": "https://domain.com/img.png",
          "name": "Lore ipsum delta bravo",
        },
        "n_answers": 1,
        "quorum": 0,
        "links": [
          "<link rel='parent' title='project' href='http://localhost:5000/api/project/1'/>"
        ],
        "calibration": 0,
        "headline": "Lore <b>ipsum</b> delta <b>bravo</b>",
        "created": "2016-05-10T11:20:45.005725",
        "rank": 0.05,
        "state": "completed",
        "link": "<link rel='self' title='task' href='http://localhost:5001/api/task/1'/>",
        "project_id": 1,
        "id": 1,
        "priority_0": 0
      },
    ]

.. note::
	When you use the fulltextsearch API the results are always sorted by rank, showing first the most relevant ones to your query.

.. note::
    We use PostgreSQL ts_rank_cd with the following configuration: ts_rank_cd(textsearch, query, 4). For more details check the official documentation of PostgreSQL.

.. note::
	By default PYBOSSA uses English for the searches. You can customize this behavior using any of the supported languages by PostgreSQL changing the settings_local.py config variable: *FULLTEXTSEARCH_LANGUAGE* = 'spanish'. 

.. note::
    By default all GET queries return a maximum of 20 objects unless the
    **limit** keyword is used to get more: limit=50. However, a maximum amount
    of 100 objects can be retrieved at once.

.. note::
    If the search does not find anything, the server will return an empty JSON
    list []


Create
------

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
------

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
------

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

Favorites
---------

Authenticated users can mark a task as a favorite. This is useful for users when they
want to see all the tasks they have done to remember them. For example, a user can mark 
as a favorite a picture that's beautiful and that he/she has marked as favorited.

For serving this purpose PYBOSSA provides the following api endpoint::

    GET /api/favorites

If the user is authenticated it will return all the tasks the user has marked as favorited. 

To add a task as a favorite, a POST should be done with a payload of {'task_id': Task.id}::

    POST /api/favorites

For removing one task from the favorites, do a DELETE::

    DEL /api/favorites/task.id

Be sure to have always the user authenticated, otherwise the user will not be able to see it.

Requesting a new task for current user
--------------------------------------

You can request a new task for the current user (anonymous or authenticated)
by::

    GET http://{pybossa-site-url}/api/{project.id}/newtask

This will return a domain Task object in JSON format if there is a task
available for the user, otherwise it will return **None**.

You can also use **limit** to get more than 1 task for the user like this::

    GET http://{pybossa-site-url}/api/{project.id}/newtask?limit=100

That query will return 100 tasks for the user. 

.. note::
    That's the maximum of tasks that a user can get at once. If you pass an argument of 200,
    PYBOSSA will convert it to 100.

You can also, use **offset** to get the next tasks, if you want, allowing you to preload::

    GET http://{pybossa-site-url}/api/{project.id}/newtask?offset=1

That query will return the next task for the user, once it solves the previous task.

Both arguments, limit and offset can be used together::


    GET http://{pybossa-site-url}/api/{project.id}/newtask?limit=2offset=2

That will load the next two tasks for the user.


Also you can request the tasks to be sorted by a Task attribute (like ID, created, etc.) using the following
arguments: **orderby** and **desc** to sort them in descending order::


    GET http://{pybossa-site-url}/api/{project.id}/newtask?orderby=priority_0&desc=true


That query will return the tasks order by priority in descending order, in other words, it will return first
the tasks with higher priority.


Requesting the user's oAuth tokens
----------------------------------

A user who has registered or signed in with any of the third parties supported
by PYBOSSA (currently Twitter, Facebook and Google) can request his own oAuth
tokens by doing::

    GET http://{pybossa-site-url}/api/token?api_key=API-KEY

Additionally, the user can specify any of the tokens if only its retrieval is
desired::

    GET http://{pybossa-site-url}/api/token/{provider}?api_key=API-KEY

Where 'provider' will be any of the third parties supported, i.e. 'twitter',
'facebook' or 'google'.

Using your own user database
----------------------------

Since version v2.3.0 PYBOSSA supports external User IDs. This means that you can
easily use your own database of users without having to registering them in the
PYBOSSA server. As a benefit, you will be able to track your own users within the
PYBOSSA server providing a very simple and easy experience for them.

A typical case for this would be for example a native phone app (Android, iOS or Windows).

Usually phone apps have their own user base. With this in mind, you can add a crowdsourcing
feature to your phone app by just using PYBOSSA in the following way.

First, create a project. When you create a project in PYBOSSA the system will create for
you a *secret key*. This secret key will be used by your phone app to authenticate all
the requests and avoid other users to send data to your project via external user API.


.. note::

    We highly recommend using SSL on your server to secure all the process. You can use
    Let's Encrypt certificates for free. Check their `documentation. <https://certbot.eff.org/>`_

Now your phone app will have to authenticate to the server to get tasks and post task runs.

To do it, all you have to do is to create an HTTP Request with an Authorization Header like this::

    HEADERS Authorization: project.secret_key
    GET http://{pybossa-site-url}/api/auth/project/short_name/token

That request will return a JWT token for you. With that token, you will be able to start
requesting tasks for your user base passing again an authorization header. Imagine a user
from your database is identified like this: '1xa'::

    HEADERS Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ
    GET http://{pybossa-site-url}/api/{project.id}/newtask?external_uid=1xa


That will return a task for the user ID 1xa that belongs to your database but not to
PYBOSSA. Then, once the user has completed the task you will be able to submit it like
this::

    HEADERS Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ
    POST http://{pybossa-site-url}/api/taskrun?external_uid=1xa


.. note::
    The TaskRun object needs to have the external_uid field filled with 1xa.

As simple as that!

.. _disqus-api:

Disqus Single Sign On (SSO)
---------------------------

If the PYBOSSA server is configured with Disqus SSO keys (see :ref:`disqus`), then you can
get the authentication parameters in this endpoint: *api/disqus/sso*

The endpoint will return a JSON object with two keys: *api_key* and *remote_auth_s3*. Use those values to authenticate the user in Disqus. Check their official documentation_.

.. `Disqus SSO`: customizing.html#disqus-single-sign-on-sso
.. _documentation:  https://help.disqus.com/customer/portal/articles/236206


User api endpoint
----------------

While all the other endpoints behave the same, this one is a bit special as we deal with private information
like emails. 

Anonymous users
~~~~~~~~~~~~~~~

The following actions cannot be done:

#. Create a new user via a POST
#. Update an existing user via a PUT
#. Delete an existing user via a DEL

Read action will only return user name and locale for that user.

Authenticated users
~~~~~~~~~~~~~~~~~~~

The following actions cannot be done:

#. Create a new user via a POST
#. Update an existing user via a PUT different than the same user
#. Delete an existing user via a DEL


Read action will only return user name and locale for that user. If the user access its own page, then
all the information will be available to him/her.

Admin users
~~~~~~~~~~~

The following actions cannot be done:

#. Create a new user via a POST
#. Delete an existing user via a DEL

Read action can be done on any user. The admins will have access to the User IDs. This will be helpful in
case that you want to give, for example badges, for users when using our webhooks solution. Each user has
in the info field a new field named **extra** where that information (or anything else) could be stored.

Command line Example Usage of the API
-------------------------------------

Create a Project object:

.. code-block:: bash

    curl -X POST -H "Content-Type:application/json" -s -d '{"name":"myproject", "info":{"xyz":1}}' 'http://localhost:5000/api/project?api_key=API-KEY'

PYBOSSA endpoints
-----------------

The following endpoints of PYBOSSA server can be requested setting the header *Content-Type* to *application/json* so you can retrieve the data using JavaScript.

.. note::
    If a key has the value **null** is because, that view is not populating that specific field. However, that value should be retrieved in a different one. Please, see all the documentation.

Account index
~~~~~~~~~~~~~

**Endpoint: /account/page/<int:page>**

*Allowed methods*: **GET**

**GET**

It returns a JSON object with the following information:

* **accounts**: this key holds the list of accounts for the given page.
* **pagination**: this key holds the pagination information.
* **top_users**: this key holds the top users (including the user if authenticated) with their rank and scores.
* **update_feed**: the latest actions in the server (users created, contributions, new tasks, etc.).
* **template**: the Jinja2 template that should be rendered in case of text/html.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "accounts": [
        {
          "created": "2015-06-10T15:02:38.411497",
          "fullname": "Scifabric",
          "info": {
            "avatar": "avatar.png",
            "container": "user_234234dd3"
          },
          "locale": null,
          "name": "Scifabric",
          "rank": null,
          "registered_ago": "1 year ago",
          "score": null,
          "task_runs": 3
        },
      ],
      "pagination": {
        "next": true,
        "page": 3,
        "per_page": 24,
        "prev": true,
        "total": 11121
      },
      "template": "account/index.html",
      "title": "Community",
      "top_users": [
        {
          "created": "2014-08-17T18:28:56.738119",
          "fullname": "Buzz Bot",
          "info": {
            "avatar": "avatar.png",
            "container": "user_55"
          },
          "locale": null,
          "name": "buzzbot",
          "rank": 1,
          "registered_ago": null,
          "score": 54247,
          "task_runs": null
        },
      ],
      "total": 11121,
      "update_feed": []
    }

Account registration
~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/register**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **form**: The form fields that need to be sent for creating an account. It contains the CSRF token for validating the POST, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title of the page.

**Example output**

.. code-block:: python

    {
      "form": {
        "confirm": null,
        "csrf": "token,"
        "email_addr": null,
        "errors": {},
        "fullname": null,
        "name": null,
        "password": null
      },
      "template": "account/register.html",
      "title": "Register"
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **next**: URL that you JavaScript can follow as a redirect. It is not mandatory.

**Example output**

.. code-block:: python

    {
        "next":"/about"
    }


If there's an error in the form fields, you will get them in the **form.errors** key:

.. code-block:: python

    {
      "form": {
        "confirm": "daniel",
        "csrf": "token",
        "email_addr": "daniel",
        "errors": {
          "email_addr": [
            "Invalid email address."
          ],
          "name": [
            "The user name is already taken"
          ]
        },
        "fullname": "daniel",
        "name": "daniel",
        "password": "daniel"
      },
      "template": "account/register.html",
      "title": "Register"
    }

If email confirmation is required for registering you will get this account validation
result when all input data is correct. Note: Keep in mind that account is not
created fully until the user confirmed his email.

.. code-block:: python

    {
      "status": "sent",
      "template": "account/account_validation.html",
      "title": "Account validation"
    }

Account sign in
~~~~~~~~~~~~~~~
**Endpoint: /account/signin**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **auth**: list of supported authentication methods using different social networks like Google, Facebook and Twitter.
* **form**: the form fields that need to be sent for signing a user. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.

**Example output**

.. code-block:: python

    {
      "auth": {
        "facebook": true,
        "google": true,
        "twitter": true
      },
      "form": {
        "csrf": "token",
        "email": null,
        "errors": {},
        "password": null
      },
      "next": null,
      "template": "account/signin.html",
      "title": "Sign in"
    }


**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **form**: the form fields with the sent information. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.

**Example output**

.. code-block:: python

    {
      "auth": {
        "facebook": true,
        "google": true,
        "twitter": true
      },
      "flash": "Please correct the errors",
      "form": {
        "csrf": "token",
        "email": "prueba@prueba.com",
        "errors": {
          "password": [
            "You must provide a password"
          ]
        },
        "password": ""
      },
      "next": null,
      "status": "error",
      "template": "account/signin.html",
      "title": "Sign in"
    }


If the login is successful, then, you will get something like this:

.. code-block:: python

    {
      "flash": "Welcome back John Doe",
      "next": "/",
      "status": "success"
    }

Account sign out
~~~~~~~~~~~~~~~~
**Endpoint: /account/signout**

*Allowed methods*: **GET**

It returns a JSON object with the following information:

* **next**: suggested redirection after the sign out.
* **message**: message displaying `success` for sign out.

Account recover password
~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/forgot-password**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **form**: the form fields that need to be sent for creating an account. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.

**Example output**

.. code-block:: python

    {
      "form": {
        "csrf": "token,"
        "email_addr": null
      },
      "template": "account/password_forgot.html"
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **form**: the form fields with the sent information. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.

**Example output**

.. code-block:: python

    {
      "flash": [
        "We don't have this email in our records. You may have signed up with a different email or used Twitter, Facebook, or Google to sign-in"
      ],
      "form": {
        "csrf": "1483549683.06##cc1c7ff101b2a14a89cac5462e5028e6235ddb31",
        "email_addr": "algo@algo.com",
        "errors": {}
      },
      "template": "/account/password_forgot.html"
    }

If there's an error in the form fields, you will get them in the **form.errors** key:

.. code-block:: python

    {
      "flash": "Something went wrong, please correct the errors on the form",
      "form": {
        "csrf": "1483552042.97##f0e36b1b113934532ff9c8003b120365ff45f5e4",
        "email_addr": "algoom",
        "errors": {
          "email_addr": [
            "Invalid email address."
          ]
        }
      },
      "template": "/account/password_forgot.html"
    }

Account name
~~~~~~~~~~~~
**Endpoint: /account/<name>

*Allowed methods*: **GET**

**GET**

It returns a JSON object with the following information:

* **projects_contrib**: a list of projects the user has contributed too.
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.
* **user**: User information, including fullname, rank etc.

**Example output**

If you are not logged in or requesting details of another user you will only get public viewable information. If you are logged in you will also get private information in the user field. Sample output of public information:

.. code-block:: python

    {
        "projects_contrib": [
            {
                "description": "this is a project",
                "info": {
                    "container": "123",
                    "thumbnail": "thumbnailx"
                },
                "n_tasks": 4,
                "n_volunteers": 0,
                "name": "test12334",
                "overall_progress": 0,
                "short_name": "test12334"
            }
        ],
        "projects_created": [
            {
                "description": "Youtube 1",
                "info": {
                    "container": "345",
                    "thumbnail": "thumbnaily"
                },
                "n_tasks": 15,
                "n_volunteers": 0,
                "name": "JohnDoe Youtube 1",
                "overall_progress": 0,
                "short_name": "johnyoutube1"
            },
        ]
        "template": "/account/public_profile.html",
        "title": "John &middot; User Profile",
        "user": {
            "fullname": "Joen Doe",
            "info": {
                "container": "user_4953"
            },
            "n_answers": 56,
            "name": "JohnDoe",
            "rank": 1813,
            "score": 56
        }
    }

Example of logged in user:

.. code-block:: python

    {
        ...
        "user": {
            "api_key": "aa3ee485-896d-488a-83f7-88a29bf45171",
            "confirmation_email_sent": false,
            "created": "2014-08-11T08:59:32.079599",
            "email_addr": "johndoe@johndoe.com",
            "facebook_user_id": null,
            "fullname": "John Doe",
            "google_user_id": null,
            "id": 4953,
            "info": {
                "container": "user_4953"
            },
            "n_answers": 56,
            "name": "JohnDoe",
            "rank": 1813,
            "registered_ago": "2 years ago",
            "score": 56,
            "total": 10046,
            "twitter_user_id": null,
            "valid_email": true
        }
    }

Account profile
~~~~~~~~~~~~~~~
**Endpoint: /account/profile

*Allowed methods*: **GET**

**GET**

If logged in you will get the same information as on /account/<name> (see above). If you are not logged in you will get the following example output

**Example output**

.. code-block:: python

    {
      "next": "/account/signin",
      "status": "not_signed_in"
    }

Account projects
~~~~~~~~~~~~~~~~
**Endpoint: /account/<name>/projects**

*Allowed methods*: **GET**

**GET**

The user needs to be logged in. It returns a JSON object with the following information:

* **projects_draft**: a list of draft projects of the user.
* **projects_published**: a list of published projects of the user.
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.

**Example output**

.. code-block:: python

    {
      "projects_draft": [
        {
          "description": "This should be the Youtube Project",
          "id": 3169,
          "info": {
            "task_presenter": "..."
          },
          "n_tasks": 0,
          "n_volunteers": 0,
          "name": "Youtube_Test1",
          "overall_progress": 0,
          "owner_id": 4953,
          "short_name": "youtube_test1"
        },
        ...
      ],
      "projects_published": [
        {
          "description": "Youtube 1",
          "id": 3206,
          "info": {
            "results": "",
            "task_presenter": ".."
            "tutorial": ""
          },
          "n_tasks": 15,
          "n_volunteers": 0,
          "name": "Youtube 1",
          "overall_progress": 0,
          "owner_id": 4953,
          "short_name": "youtube1"
        },
        ...
      ],
      "template": "account/projects.html",
      "title": "Projects"
    }

Account update profile
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/<name>/update**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **form**: the form fields that need to be sent for updating account. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **password_form**: the form fields that need to be sent for updating the account's password. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **upload_form**: the form fields that need to be sent for updating the account's avatar. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.

**Example output**

.. code-block:: python

    {
      "flash": null,
      "form": {
        "ckan_api": null,
        "csrf": "token",
        "email_addr": "email@emai.com",
        "errors": {},
        "fullname": "John Doe",
        "id": 0,
        "locale": "en",
        "name": "johndoe",
        "privacy_mode": true,
        "subscribed": true
      },
      "password_form": {
        "confirm": null,
        "csrf": "token",
        "current_password": null,
        "errors": {},
        "new_password": null
      },
      "show_passwd_form": true,
      "template": "/account/update.html",
      "title": "Update your profile: John Doe",
      "upload_form": {
        "avatar": null,
        "csrf": "token",
        "errors": {},
        "id": null,
        "x1": 0,
        "x2": 0,
        "y1": 0,
        "y2": 0
      }
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

As this endpoint supports **three** different forms, you must specify which form are
you targetting adding an extra key: **btn**. The options for this key are:

* **Profile**: to update the **form**.
  **Upload**: to update the **upload_form**.
  **Password**: to update the **password_form**.
  **External**: to update the **form** but only the external services.

.. note::
    Be sure to respect the Uppercase in the first letter, otherwise it will fail.

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **form**: the form fields with the sent information. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.

**Example output**

.. code-block:: python

    {
      "flash": "Your profile has been updated!",
      "next": "/account/pruebaadfadfa/update",
      "status": "success"
    }


If there's an error in the form fields, you will get them in the **form.errors** key:

.. code-block:: python

    {
      "flash": "Please correct the errors",
      "form": {
        "ckan_api": null,
        "csrf": "token",
        "email_addr": "pruebaprueba.com",
        "errors": {
          "email_addr": [
            "Invalid email address."
          ]
        },
        "fullname": "prueba de json",
        "id": 0,
        "locale": "es",
        "name": "pruebaadfadfa",
        "privacy_mode": true,
        "subscribed": true
      },
      "password_form": {
        "confirm": "",
        "csrf": "token",
        "current_password": "",
        "errors": {},
        "new_password": ""
      },
      "show_passwd_form": true,
      "template": "/account/update.html",
      "title": "Update your profile: John Doe",
      "upload_form": {
        "avatar": "",
        "csrf": "token",
        "errors": {},
        "id": 0,
        "x1": 0,
        "x2": 0,
        "y1": 0,
        "y2": 0
      }
    }

.. note::
    For updating the avatar is very important to not set the *Content-Type*. If you
    are using jQuery, set it to False, so the file is handled properly.

    The (x1,x2,y1,y2) are the coordinates for cutting the image and create the avatar.

    (x1,y1) are the offset left of the cropped area and  the offset top of the cropped
    area respectively; and (x2,y2) are the width and height of the crop.


Account reset password
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/reset-password**

*Allowed methods*: **GET/POST**

**GET**

*Required arguments*:  **key** a string required to validate the link for updating
the password of the user. This key is sent to the user via email after requesting to
reset the password.

It returns a JSON object with the following information:

* **form**: the form fields that need to be sent for updating account. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.

**Example output**

.. code-block:: python

    {
      "form": {
        "confirm": null,
        "csrf": "token",
        "current_password": null,
        "errors": {},
        "new_password": null
      },
      "template": "/account/password_reset.html"

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **status**: A status message, indicating if something went wrong.
* **next**: Suggested URL to redirect the user.

**Example output**

.. code-block:: python

    {
        u'status': u'success',
        u'flash': u'You reset your password successfully!',
        u'next': u'/'
    }

Account reset API Key
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/<user>/resetapikey**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **csrf**: The CSRF token for validating the post.

**Example output**

.. code-block:: python

    {
        "form":
            {
                "csrf": "token",
            }
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **status**: A status message, indicating if something went wrong.
* **next**: Suggested URL to redirect the user.

**Example output**

.. code-block:: python

    {
        u'status': u'success',
        u'flash': u'New API-KEY generated',
        u'next': u'/account/<user>'
    }


Account subscribe to newsletter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/newsletter

*Allowed methods*: **GET**

**GET**

It returns a JSON object with the following information:

* **template**: The template that Jinja2 will render.
* **title**: The title of the endpoint.
* **next**: The next URL.

**Example output**

.. code-block:: python

    {
        "template": "account/newsletter.html",
        "title": "Subscribe to our Newsletter",
        "next": "/"
    }

If you want to subscribe a user, then you have to call the same endpoint with
the following argument: *subscribe=true*

**Example output**

.. code-block:: python

    {
        "flash": "You are subscribed to our newsletter",
        "status": "success",
        "next": "/"
    }

Account confirm email
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /account/confirm-email**

*Allowed methods*: **GET**

**GET**

If account validation is enabled, then, using this endpoint the user will receive an email
to validate its account. It returns a JSON object with the following information:

* **flash**: A message stating that an email has been sent.
* **status**: The status of the call.
* **next**: The next url.

**Example output**

.. code-block:: python

    {
        "flash": 'Ane email has been sent to validate your e-mail address.',
        'status': 'info',
        'next': '/account/<username>/'
    }


Home
~~~~
**Endpoint: /**

*Allowed methods*: **GET**

**GET**

It returns a JSON object with the following information:

* **top_projects**: A list of the most active projects.
* **categories_projects**: A dictionary with all the published categories and its associated projects.
* **categories**: All the available categories.
* **template**: Jinja2 template.
* **top_users**: List of top contributors.

**Example output**

.. code-block:: python

    {
      "categories": [
        {
          "created": null,
          "description": null,
          "id": null,
          "name": "Featured",
          "short_name": "featured"
        },
        {
          "description": "Economic projects",
          "id": 6,
          "name": "Economics",
          "short_name": "economics"
        },
      ],
      "categories_projects": {
        "economics": [
          {
            "description": "Description",
            "info": {
              "container": "user",
              "thumbnail": "415602833.png"
            },
            "n_tasks": 18,
            "n_volunteers": 26,
            "name": "Man made objects identity",
            "overall_progress": 0,
            "short_name": "manmadeobjectsidentity"
          },
        ],
      },
      "template": "/home/index.html",
      "top_projects": [
        {
          "description": "Image pattern recognition",
          "info": {
            "container": "user",
            "thumbnail": "772569.58.png"
          },
          "n_tasks": null,
          "n_volunteers": 17499,
          "name": "Name",
          "overall_progress": null,
          "short_name": "name"
        },
      ],
      "top_users": [
        {
          "created": "2014-08-17T18:28:56.738119",
          "fullname": "John Doe",
          "info": {
            "avatar": "1410771tar.png",
            "container": "05"
          },
          "n_answers": null,
          "name": "johndoe",
          "rank": 1,
          "registered_ago": null,
          "score": 54247
        },
      ]
    }

Project shortname
~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/**

*Allowed methods*: **GET**

**GET**

Shows project information and owner information.

If you are not the owner of the project or anonymous then you will get only
public available information for the owner and the project itself.

* **last_activity**: Last activity on the project.
* **n_completed_tasks**: Number of completed tasks.
* **n_task_runs**: Number of task runs.
* **n_tasks**: Number of tasks.
* **n_volunteers**: Number of volunteers.
* **overall_progress**: Overall progress.
* **owner**: Owner user information.
* **pro_features**: Enabled pro features for the project.
* **project**: Project information
* **template**: Jinja2 template.
* **title**: the title for the endpoint.

**Example output**

for logged in user JohnDoe:

.. code-block:: python

    {
      "last_activity": "2015-01-21T12:01:41.209270",
      "n_completed_tasks": 0,
      "n_task_runs": 3,
      "n_tasks": 8,
      "n_volunteers": 1,
      "overall_progress": 0,
      "owner": {
        "api_key": "akjhfd85-8afd6-48af-f7afg-kjhsfdlkjhf1",
        "confirmation_email_sent": false,
        "created": "2014-08-11T08:59:32.079599",
        "email_addr": "johndoe@johndoe.com",
        "facebook_user_id": null,
        "fullname": "John Doe",
        "google_user_id": null,
        "id": 1234,
        "info": {
          "container": "user_1234"
        },
        "n_answers": 56,
        "name": "JohnDoe",
        "rank": 1813,
        "registered_ago": "2 years ago",
        "score": 56,
        "total": 11093,
        "twitter_user_id": null,
        "valid_email": true
      },
      "pro_features": {
        "auditlog_enabled": true,
        "autoimporter_enabled": true,
        "webhooks_enabled": true
      },
      "project": {
        "allow_anonymous_contributors": true,
        "category_id": 2,
        "contacted": true,
        "contrib_button": "can_contribute",
        "created": "2015-01-21T11:59:36.519541",
        "description": "flickr678",
        "featured": false,
        "id": 4567,
        "info": {
          "task_presenter": "<div> .... "
        },
        "long_description": "flickr678\r\n",
        "n_blogposts": 0,
        "n_results": 0,
        "name": "flickr678",
        "owner_id": 9876,
        "published": true,
        "secret_key": "veryverysecretkey",
        "short_name": "flickr678",
        "updated": "2016-04-13T08:07:38.897626",
        "webhook": null
      },
      "template": "/projects/project.html",
      "title": "Project: flickr678"
    }

Anonymous and other user output:

.. code-block:: python

    {
      "last_activity": "2015-01-21T12:01:41.209270",
      "n_completed_tasks": 0,
      "n_task_runs": 3,
      "n_tasks": 8,
      "n_volunteers": 1,
      "overall_progress": 0,
      "owner": {
        "created": "2014-08-11T08:59:32.079599",
        "fullname": "John Doe",
        "info": {
          "avatar": null,
          "container": "user_4953"
        },
        "n_answers": 56,
        "name": "JohnDoe",
        "rank": 1813,
        "registered_ago": "2 years ago",
        "score": 56
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "created": "2015-01-21T11:59:36.519541",
        "description": "flickr678",
        "id": 4567,
        "info": {
          "container": null,
          "thumbnail": null
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "flickr678",
        "overall_progress": null,
        "owner": null,
        "short_name": "flickr678",
        "updated": "2016-04-13T08:07:38.897626"
      },
      "template": "/projects/project.html",
      "title": "Project: flickr678"
    }

Project settings
~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/settings**

*Allowed methods*: **GET**

**GET**

Shows project information and owner information.
Only works for authenticated users for their own projects (or admins).
Anonymous users will get a 302 to login page.
Logged in users with access rights will get a 403 when it's not their own project.

* **last_activity**: Last activity on the project.
* **n_completed_tasks**: Number of completed tasks.
* **n_task_runs**: Number of task runs.
* **n_tasks**: Number of tasks.
* **n_volunteers**: Number of volunteers.
* **overall_progress**: Overall progress.
* **owner**: Owner user information.
* **pro_features**: Enabled pro features for the project.
* **project**: Project information
* **template**: Jinja2 template.
* **title**: the title for the endpoint.

The example output matches **/project/<short_name>/**

Project results
~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/results**

*Allowed methods*: **GET**

**GET**

Shows information about a project results template.
If the logged in user is the owner of the project you will get more detailed
owner information and project information.

* **last_activity**: Last activity on the project.
* **n_completed_tasks**: Number of completed tasks.
* **n_results**: Number of results
* **n_task_runs**: Number of task runs.
* **n_tasks**: Number of tasks.
* **n_volunteers**: Number of volunteers.
* **overall_progress**: Overall progress.
* **owner**: Owner user information.
* **pro_features**: Enabled pro features for the project.
* **project**: Project information
* **template**: Jinja2 template for results
* **title**: the title for the endpoint.

**Example output**

for anonymous user or when you are not the project owner:

.. code-block:: python

    {
      "last_activity": "2015-01-21T12:01:41.209270",
      "n_completed_tasks": 0,
      "n_results": 0,
      "n_task_runs": 3,
      "n_tasks": 8,
      "n_volunteers": 1,
      "overall_progress": 0,
      "owner": {
        "created": "2014-08-11T08:59:32.079599",
        "fullname": "John",
        "info": {
          "avatar": null,
          "container": "user_4953"
        },
        "n_answers": 56,
        "name": "JohnDoe",
        "rank": 1813,
        "registered_ago": "2 years ago",
        "score": 56
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "created": "2015-01-21T11:59:36.519541",
        "description": "flickr678",
        "featured": false,
        "id": 2417,
        "info": {
          "container": null,
          "thumbnail": null
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "flickr678",
        "overall_progress": null,
        "owner": null,
        "short_name": "flickr678",
        "updated": "2016-04-13T08:07:38.897626"
      },
      "template": "/projects/results.html",
      "title": "Project: flickr678"
    }

Project stats
~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/stats**

*Allowed methods*: **GET**

**GET**

Shows project statistics if available.

If you are not the owner of the project or anonymous then you will get only
public available information for the owner and the project itself.

* **avg_contrib_time**: Average contribution time (NOT existing when no statistics there!).
* **projectStats**: Project statistics (NOT existing when no statistics there!).
* **userStats**: User statistics (NOT existing when no statistics there!).
* **n_completed_tasks**: Number of completed tasks.
* **n_tasks**: Number of tasks.
* **n_volunteers**: Number of volunteers.
* **overall_progress**: Progress (0..100).
* **owner**: Owner user information
* **pro_features**: Enabled pro features for the project.
* **project**: Project information
* **template**: Jinja2 template.
* **title**: the title for the endpoint.


**Example output**
Statistics are existing in this output:

.. code-block:: python

    {
      "avg_contrib_time": 0,
      "n_completed_tasks": 2,
      "n_tasks": 2,
      "n_volunteers": 59,
      "overall_progress": 100,
      "owner": {
        "created": "2012-06-06T06:27:18.760254",
        "fullname": "Daniel Lombraña González",
        "info": {
          "avatar": "1422360933.8_avatar.png",
          "container": "user_3"
        },
        "n_answers": 2998,
        "name": "teleyinex",
        "rank": 66,
        "registered_ago": "4 years ago",
        "score": 2998
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "better_stats_enabled": true,
        "webhooks_enabled": false
      },
      "project": {
        "created": "2013-01-10T19:58:55.454015",
        "description": "Facial expressions that convey feelings",
        "featured": true,
        "id": 253,
        "info": {
          "container": "user_3",
          "thumbnail": "project_253_thumbnail_1460620575.png"
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "The Face We Make",
        "overall_progress": null,
        "owner": null,
        "short_name": "thefacewemake",
        "updated": "2016-04-14T07:56:16.114006"
      },
      "projectStats": "{\"userAuthStats\": {\"top5\": [], \"values\": [], \"label\": \"Authenticated Users\"} ...",
      "template": "/projects/stats.html",
      "title": "Project: The Face We Make &middot; Statistics",
      "userStats": {
        "anonymous": {
          "pct_taskruns": 0,
          "taskruns": 0,
          "top5": [],
          "users": 0
        },
        "authenticated": {
          "pct_taskruns": 0,
          "taskruns": 0,
          "top5": [],
          "users": 0
        },
        "geo": false
      }
    }

Project tasks
~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/tasks**

*Allowed methods*: **GET**

**GET**

Shows project tasks.

If you are not the owner of the project or anonymous then you will get only
public available information for the owner and the project itself.

* **autoimporter_enabled**: If autoimporter is enabled.
* **last_activity**: Last activity.
* **n_completed_tasks**: Number of completed tasks.
* **n_task_runs**: Number of task runs.
* **n_tasks**: Number of tasks.
* **n_volunteers**: Number of volunteers.
* **overall_progress**: Progress (0..100).
* **owner**: Owner user information
* **pro_features**: Enabled pro features for the project.
* **project**: Project information.
* **template**: Jinja2 template.
* **title**: the title for the endpoint.

**Example output**

for another project where you are not the owner:

.. code-block:: python

    {
      "autoimporter_enabled": true,
      "last_activity": "2017-03-02T21:00:33.627277",
      "n_completed_tasks": 184839,
      "n_task_runs": 1282945,
      "n_tasks": 193090,
      "n_volunteers": 20016,
      "overall_progress": 95,
      "owner": {
        "created": "2014-02-13T15:28:08.420187",
        "fullname": "John Smith",
        "info": {
          "avatar": "1410769844.15_avatar.png",
          "container": "user_3927",
          "extra": null
        },
        "locale": null,
        "n_answers": 43565,
        "name": "pmisson",
        "rank": 3,
        "registered_ago": "3 years ago",
        "score": 43565
      },
      "pro_features": {
        "auditlog_enabled": true,
        "autoimporter_enabled": true,
        "webhooks_enabled": true
      },
      "project": {
        "created": "2014-02-22T15:09:23.691811",
        "description": "Image pattern recognition",
        "featured": true,
        "id": 1377,
        "info": {
          "container": "user_3927",
          "thumbnail": "app_1377_thumbnail_1410772569.58.png"
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "Cool Project",
        "overall_progress": null,
        "owner": null,
        "short_name": "coolproject",
        "updated": "2017-03-02T21:00:33.965587"
      },
      "template": "/projects/tasks.html",
      "title": "Project: Cool project"
    }

Project task id
~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/task/<int:task_id>**

*Allowed methods*: **GET**

**GET**

Shows a project task based on id.

If you are not the owner of the project or anonymous then you will get only
public available information for the owner and the project itself.

* **owner**: Owner user information
* **project**: Project information.
* **template**: Jinja2 template of the task HTML template.
* **title**: the title for the endpoint.

**Example output**

for another project where you are not the owner:

.. code-block:: python

    {
      "owner": {
        "created": "2014-08-11T08:59:32.079599",
        "fullname": "John Doe",
        "info": {
          "avatar": "1458638093.9_avatar.png",
          "container": "user_4953",
          "extra": null
        },
        "locale": null,
        "n_answers": 257,
        "name": "JohnD",
        "rank": 840,
        "registered_ago": "2 years ago",
        "score": 257
      },
      "project": {
        "created": "2015-01-21T11:59:36.519541",
        "description": "flickr678",
        "featured": false,
        "id": 2417,
        "info": {
          "container": null,
          "thumbnail": null
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "flickr678",
        "overall_progress": null,
        "owner": null,
        "short_name": "flickr678",
        "updated": "2017-03-22T13:03:55.496660"
      },
      "template": "/projects/presenter.html",
      "title": "Project: flickr678 &middot; Contribute"
    }


Leaderboard
~~~~~~~~~~~
**Endpoint: /leaderboard/**
**Endpoint: /leaderboard/window/<int:window>**

*Allowed methods*: **GET**

**GET**

Shows you the top 20 contributors rank in a sorted leaderboard.
If you are logged in you will also get the rank of yourself even when you are
not visible on the top public leaderboard.

By default the window is zero, adding the authenticated user to the bottom of the
top 20, so the user can know the rank. If you want, you can use a window to show
the previous and next users taking into account authenticated user rank. For example,
you can get the previous 3 and next 3 accessing this URL: /leaderboard/window/3.

* **template**: Jinja2 template.
* **title**: the title for the endpoint.
* **top_users**: Sorted list of leaderboard top users.

**Example output**

for logged in user JohnDoe (normally not visible in public leaderboard):

.. code-block:: python

    {
        "template": "/stats/index.html",
        "title": "Community Leaderboard",
        "top_users": [
            {
                "created": "2014-08-17T18:28:56.738119",
                "fullname": "Buzz Bot",
                "info": {
                    "avatar": "1410771548.09_avatar.png",
                    "container": "user_5305"
                },
                "n_answers": null,
                "name": "buzzbot",
                "rank": 1,
                "registered_ago": null,
                "score": 54259
            },
            ... ,
            {
                "created": "2014-08-11T08:59:32.079599",
                "fullname": "JohnDoe",
                "info": {
                    "avatar": null,
                    "container": "user_4953"
                },
                "n_answers": null,
                "name": "JohnDoe",
                "rank": 1813,
                "registered_ago": null,
                "score": 56
            }
        ]
    }


Announcements
~~~~~~~~~~~~~
**Endpoint: /announcements/**

*Allowed methods*: **GET**

**GET**

Shows you PYBOSSA wide announcements

* **announcements**: Announcements
* **template**: the rendered Announcements tamplate (currently empty)

**Example output**

.. code-block:: python

    {
        "announcements": [
            {
                "body": "test123",
                "created": "2017-05-31T15:23:44.858735",
                "id": 5,
                "title": "title123",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-05-31T15:23:28.477516",
                "id": 4,
                "title": "blogpost title",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-06-01T23:42:45.042010",
                "id": 7,
                "title": "blogpost title",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-06-01T23:45:11.612801",
                "id": 8,
                "title": "blogpost title",
                "user_id": 4953
            }
        ],
        "template": ""
    }


Admin announcement
~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/announcement**

**GET**

Shows you PYBOSSA wide announcements

* **announcements**: Announcements
* **csrf**: csrf token
* **template**: the rendered Announcements tamplate (currently empty)
* **title**: title of rendered endpoint

**Example output**

.. code-block:: python

    {
        "announcements": [
            {
                "body": "test123",
                "created": "2017-05-31T15:23:44.858735",
                "id": 5,
                "title": "title123",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-05-31T15:23:28.477516",
                "id": 4,
                "title": "blogpost title",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-06-01T23:42:45.042010",
                "id": 7,
                "title": "blogpost title",
                "user_id": 4953
            },
            {
                "body": "new body",
                "created": "2017-06-01T23:45:11.612801",
                "id": 8,
                "title": "blogpost title",
                "user_id": 4953
            }
        ],
      "csrf": "1496394861.12##1bfcbb386bae5d1625c023a23b08865b4176579d",
      "template": "",
      "title": "Manage global Announcements"
    }


Admin announcement new
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/announcement/new**

*Allowed methods*: **GET/POST**

**GET**

Creates a new PYBOSSA wide announcement

* **form**: form input
* **template**: the rendered Announcements tamplate (currently empty)
* **title**: title of rendered endpoint


**Example output**

.. code-block:: python

    {
      "form": {
        "body": null,
        "csrf": "1496394903.81##bb5fb0c527955073ec9ad694ed9097e7c868272a",
        "errors": {},
        "title": null
      },
      "template": "",
      "title": "Write a new post"
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".
On success you will get a 200 http code and following output:

**Example output**

.. code-block:: python

    {
      "flash": "<i class=\"icon-ok\"></i> Annnouncement created!",
      "next": "/admin/announcement",
      "status": "success"
    }


Admin announcement update
~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/announcement/<id>/update**

*Allowed methods*: **GET/POST**

**GET**

Updates a PYBOSSA announcement

* **form**: form input
* **template**: the rendered Announcements tamplate (currently empty)
* **title**: title of rendered endpoint


**Example output**

.. code-block:: python

    {
      "form": {
        "body": "test6",
        "csrf": "1496328993.27##aa51e026938129afdfb0e6a5eab8c6b9427f81f6",
        "errors": {},
        "id": 4,
        "title": "test6"
      },
      "template": "",
      "title": "Edit a post"
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".
On success you will get a 200 http code and following output:

**Example output**

.. code-block:: python

    {
      "flash": "<i class=\"icon-ok\"></i> Announcement updated!",
      "next": "/admin/announcement",
      "status": "success"
    }


Admin announcement delete
~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/announcement/<id>/delete**

*Allowed methods*: **POST**

Deletes a PYBOSSA announcement

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken". You can get the token from /admin/announcement
On success you will get a 200 http code and following output:

**Example output**

.. code-block:: python

    {
      "flash": "<i class=\"icon-ok\"></i> Announcement deleted!",
      "next": "/admin/announcement",
      "status": "success"
    }


Admin users
~~~~~~~~~~~
**Endpoint: /admin/users**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **form**: A form for searching for users.
* **found**: A list of found users according to a search.
* **template**: Jinja2 template.
* **users**: List of admin users.

**Example output**

.. code-block:: python

    {
      "form": {
        "csrf": "token",
        "errors": {},
        "user": null
      },
      "found": [],
      "template": "/admin/users.html",
      "title": "Manage Admin Users",
      "users": [
        {
          "admin": true,
          "api_key": "key",
          "category": null,
          "ckan_api": null,
          "confirmation_email_sent": false,
          "created": "date",
          "email_addr": "email",
          "facebook_user_id": null,
          "flags": null,
          "fullname": "John Doe",
          "google_user_id": null,
          "id": 1,
          "info": {
            "avatar": "avatar.png",
            "container": "user_1"
          },
          "locale": "en",
          "name": "johndoe",
          "newsletter_prompted": false,
          "passwd_hash": "hash",
          "privacy_mode": true,
          "pro": false,
          "subscribed": true,
          "twitter_user_id": null,
          "valid_email": true
        },
      ]
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **form**: A form with the submitted search.
* **found**: A list of found users according to a search.
* **template**: Jinja2 template.
* **users**: List of admin users.

**Example output**

.. code-block:: python

    {
      "form": {
        "csrf": "token",
        "errors": {},
        "user": 'janedoe',
      },
      "found": [
            {
              "admin": false,
              "api_key": "key",
              "category": null,
              "ckan_api": null,
              "confirmation_email_sent": false,
              "created": "date",
              "email_addr": "email",
              "facebook_user_id": null,
              "flags": null,
              "fullname": "janedoe",
              "google_user_id": null,
              "id": 80,
              "info": {},
              "locale": "en",
              "name": "janedoe",
              "newsletter_prompted": false,
              "passwd_hash": "hash",
              "privacy_mode": true,
              "pro": false,
              "subscribed": true,
              "twitter_user_id": null,
              "valid_email": true
            },
      ],
      "template": "/admin/users.html",
      "title": "Manage Admin Users",
      "users": [
        {
          "admin": true,
          "api_key": "key",
          "category": null,
          "ckan_api": null,
          "confirmation_email_sent": false,
          "created": "date",
          "email_addr": "email",
          "facebook_user_id": null,
          "flags": null,
          "fullname": "John Doe",
          "google_user_id": null,
          "id": 1,
          "info": {
            "avatar": "avatar.png",
            "container": "user_1"
          },
          "locale": "en",
          "name": "johndoe",
          "newsletter_prompted": false,
          "passwd_hash": "hash",
          "privacy_mode": true,
          "pro": false,
          "subscribed": true,
          "twitter_user_id": null,
          "valid_email": true
        },
      ]
      }


Admin users add
~~~~~~~~~~~~~~~
**Endpoint: /admin/users/add/<int:user_id>**

*Allowed methods*: **GET**

**GET**

It adds a user to the admin group. It returns a JSON object with the following information:

* **next**: '/admin/users',

**Example output**

.. code-block:: python

    {
      "next": '/admin/users',
    }

.. note::

    You will need to use the /admin/users endpoint to get a list of users for adding
    deleting from the admin group.

Admin users del
~~~~~~~~~~~~~~~
**Endpoint: /admin/users/del/<int:user_id>**

*Allowed methods*: **GET**

**GET**

It removes a user from the admin group. It returns a JSON object with the following information:

* **next**: '/admin/users',

**Example output**

.. code-block:: python

    {
      "next": '/admin/users',
    }

.. note::

    You will need to use the /admin/users endpoint to get a list of users for adding
    deleting from the admin group.


Admin categories
~~~~~~~~~~~~~~~~
**Endpoint: /admin/categories**

*Allowed methods*: **GET/POST**

**GET**

It lists all the available categories. It returns a JSON object with the following information:

* **categories**: A list of categories.
* **form**: A form with the CSRF key to add a new category.
* **n_projects_per_category**: A dictionary with the number of projects per category.


**Example output**

.. code-block:: python

    {
      "categories": [
        {
          "created": null,
          "description": "Social projects",
          "id": 2,
          "name": "Social",
          "short_name": "social"
        },
        {
          "created": "2013-06-18T11:13:44.789149",
          "description": "Art projects",
          "id": 3,
          "name": "Art",
          "short_name": "art"
        },
      ],
      "form": {
        "csrf": "token",
        "description": null,
        "errors": {},
        "id": null,
        "name": null
      },
      "n_projects_per_category": {
        "art": 41,
        "social": 182
      },
      "template": "admin/categories.html",
      "title": "Categories"
    }

**POST**

It returns the same output as before, but if the form is valid, it will return
the new created Category. Use the CSRFToken for submitting the data.

* **categories**: A list of categories.
* **form**: A form with the CSRF key to add a new category.
* **n_projects_per_category**: A dictionary with the number of projects per category.


**Example output**

.. code-block:: python

    {
      "categories": [
        {
          "created": null,
          "description": "Social projects",
          "id": 2,
          "name": "Social",
          "short_name": "social"
        },
        {
          "created": "2013-06-18T11:13:44.789149",
          "description": "Art projects",
          "id": 3,
          "name": "Art",
          "short_name": "art"
        },
        {
          "created": "now",
          "description": "new",
          "id": 4,
          "name": "new",
          "short_name": "new"
        },

      ],
      "form": {
        "csrf": "token",
        "description": "new",
        "errors": {},
        "name": "new"
      },
      "n_projects_per_category": {
        "art": 41,
        "social": 182,
        "new": 0
      },
      "template": "admin/categories.html",
      "title": "Categories"
    }


Admin categories delete
~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/categories/del/<int:id>**

*Allowed methods*: **GET/POST**

**GET**

It shows the category that will be deleted. It gives you the CSRF token to do a POST
and delete it.

* **category**: The category to be deleted.
* **form**: A form with the CSRF key to add a new category.


**Example output**

.. code-block:: python

    {
      "category": {
        "created": "2017-01-24T13:08:09.873071",
        "description": "new",
        "id": 9,
        "name": "new",
        "short_name": "new"
      },
      "form": {
        "csrf": "token",
      },
      "template": "admin/del_category.html",
      "title": "Delete Category"
    }


**POST**

It shows the category that will be deleted. It gives you the CSRF token to do a POST
and delete it.

* **flash**: A human readable message about the action.
* **next**: The next URL
* **status**: The status of the POST.


**Example output**

.. code-block:: python

    {
      "flash": "Category deleted",
      "next": "/admin/categories",
      "status": "success"
    }

Admin categories update
~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/categories/update/<int:id>**

*Allowed methods*: **GET/POST**

**GET**

It shows the category that will be updated. It gives you the CSRF token to do a POST
and update it.

* **category**: The category to be deleted.
* **form**: A form with the CSRF key to add a new category.


**Example output**

.. code-block:: python

    {
      "category": {
        "created": "2017-01-24T13:08:09.873071",
        "description": "new",
        "id": 9,
        "name": "new",
        "short_name": "new"
      },
      "form": {
        "csrf": "token",
        'description': 'new',
        'errors': {},
        'id': 9,
        'name': 'new'
      },
      "template": "admin/update_category.html",
      "title": "Update Category"
    }


**POST**

It updates the category. Use the CSRF token and form fields from the previous action
to update it.

* **flash**: A human readable message about the action.
* **next**: The next URL
* **status**: The status of the POST.


**Example output**

.. code-block:: python

    {
      "flash": "Category updated",
      "next": "/admin/categories",
      "status": "success"
    }

Admin dashboard
~~~~~~~~~~~~~~~
**Endpoint: /admin/dashboard/

*Allowed methods*: **GET**

**GET**

It shows the server statistics. You can use the argument *?refresh=1* to update the
data, as this data is only updated every 24 hours.


* **active_anon_last_week**: Active number of anonymous users in the server.
* **published_projects_last_week**: Published projects from the last week.
* **new_tasks_week**: Number of new tasks created on the last week.
* **update_feed**: Activity feed of actions in the server.
* **draft_projects_last_week**: List of new draft projects created in the last week.
* **update_projects_last_week**: List of updated projects in the last  week.
* **new_users_week**: Number of new registered users in the last week.
* **new_task_runs_week**: Number of new task runs in the last week.
* **returning_users_week**: Number of returning users per number of days in a row in the last week.
* **active_users_last_week**: Number of active users in the last week.
* **wait**: This will be False if there's data, otherwise it will be True.


**Example output**

.. code-block:: python

    {
      "active_anon_last_week": {
        "labels": [
          "2016-04-28"
        ],
        "series": [
          [
            0
          ]
        ]
      },
      "active_users_last_week": {
        "labels": [
          "2016-04-28"
        ],
        "series": [
          [
            1
          ]
        ]
      },
      "draft_projects_last_week": [
        {
          "day": "2016-04-27",
          "email_addr": "email",
          "id": id,
          "owner_id": id,
          "p_name": "name",
          "short_name": "name",
          "u_name": "name"
        },
        {
          "day": "2016-04-26",
          "email_addr": "email",
          "id": id,
          "owner_id": id,
          "p_name": "name",
          "short_name": "name",
          "u_name": "name"
        }
      ],
      "new_task_runs_week": {
        "labels": [
          "2016-04-28"
        ],
        "series": [
          [
            4
          ]
        ]
      },
      "new_tasks_week": {
        "labels": [
          "2016-04-26",
          "2016-04-28"
        ],
        "series": [
          [
            57,
            4
          ]
        ]
      },
      "new_users_week": {
        "labels": [
          "2016-04-27"
        ],
        "series": [
          [
            1
          ]
        ]
      },
      "published_projects_last_week": [],
      "returning_users_week": {
        "labels": [
          "1 day",
          "2 days",
          "3 days",
          "4 days",
          "5 days",
          "6 days",
          "7 days"
        ],
        "series": [
          [
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        ]
      },
      "template": "admin/dashboard.html",
      "title": "Dashboard",
      "update_feed": [],
      "update_projects_last_week": [
        {
          "day": "2016-04-28",
          "email_addr": "email",
          "id": id,
          "owner_id": id,
          "p_name": "name",
          "short_name": "name",
          "u_name": "name"
        },
        {
          "day": "2016-04-27",
          "email_addr": "email",
          "id": id,
          "owner_id": id,
          "p_name": "name",
          "short_name": "name",
          "u_name": "name"
        },
        {
          "day": "2016-04-26",
          "email_addr": "email",
          "id": id,
          "owner_id": id,
          "p_name": "name",
          "short_name": "name",
          "u_name": "name"
        },
      ],
      "wait": false
    }

Admin featured projects
~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/featured**

*Allowed methods*: **GET**

**GET**

Gives you all featured projects on PYBOSSA.

* **categories**: Gives you a list of categories where projects can be featured.
* **form**: The form fields that need to be sent for feature and unfeature a project. It contains the CSRF token for validating the POST/DELETE.
* **projects**: Featured projects grouped by categories.
* **template**: The Jinja2 template that could be rendered.


**Example output**

.. code-block:: python

    {
      "categories": [
        {
          "created": "2013-06-18T11:13:44.789149",
          "description": "Art projects",
          "id": 3,
          "name": "Art",
          "short_name": "art"
        },
        {
          "created": "2013-06-18T11:14:54.737672",
          "description": "Humanities projects",
          "id": 4,
          "name": "Humanities",
          "short_name": "humanities"
        },
        ...
      ],
      "projects": {
        "art": [
          {
            "created": "2013-12-10T06:54:48.222642",
            "description": "Description",
            "id": 1069,
            "info": {
              "container": "user_3738",
              "thumbnail": "app_1069_thumbnail_1410772175.32.png"
            },
            "last_activity": "just now",
            "last_activity_raw": null,
            "n_tasks": 13,
            "n_volunteers": 0,
            "name": "AAAA Test",
            "overall_progress": 0,
            "owner": "John Doe",
            "short_name": "AAAATest",
            "updated": "2014-11-05T14:55:07.564118"
          },
          ...
        ]
        "humanities": [
          {
            "created": "2014-10-21T12:20:51.194485",
            "description": "test project",
            "id": 2144,
            "info": {
              "container": null,
              "thumbnail": null
            },
            "last_activity": "2 years ago",
            "last_activity_raw": "2014-10-21T12:31:51.560422",
            "n_tasks": 9,
            "n_volunteers": 2,
            "name": "zak's test",
            "overall_progress": 0,
            "owner": "John Doe Cousin",
            "short_name": "cousintest",
            "updated": "2014-11-05T14:55:07.564118"
          },
          ...
        ]
      },
      "form": {
        "csrf": "secret_token_here"
      },
      "template": "/admin/projects.html"
    }

Admin un-/feature projects
~~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /admin/featured/<int:project_id>**

*Allowed methods*: **POST / DELETE**

**POST**

Features a specific project.

To send a valid POST request you need to pass the *csrf token* in the headers. Use the following header: "X-CSRFToken".

**Example output**

On Success it will give you the project information

.. code-block:: python

    {
      "info": {
        "task_presenter": "...",
        "container": "user_3738",
        "thumbnail": "app_1069_thumbnail_1410772175.32.png"
      },
      "updated": "2017-01-24T17:21:07.545983",
      "category_id": 3,
      "description": "Description",
      "short_name": "AAAATest",
      "created": "2013-12-10T06:54:48.222642",
      "webhook": null,
      "long_description": "AAAATest\n\n",
      "featured": false,
      "allow_anonymous_contributors": true,
      "published": true,
      "secret_key": "dfgojdsfgsgd",
      "owner_id": 3738,
      "contacted": null,
      "id": 1069,
      "name": "AAAA Test"
    }

If a project is already featured:

.. code-block:: python

    {
      "code": 400,
      "description": "CSRF token missing or incorrect.",
      "template": "400.html"
    }


**DELETE**

Unfeatures a specific project.

To send a valid DELETE request you need to pass the *csrf token* in the headers. Use the following header: "X-CSRFToken".

**Example output**

On Success it will give you the project information

.. code-block:: python

    {
      "info": {
        "task_presenter": "...",
        "container": "user_3738",
        "thumbnail": "app_1069_thumbnail_1410772175.32.png"
      },
      "updated": "2017-01-24T17:21:07.545983",
      "category_id": 3,
      "description": "Description",
      "short_name": "AAAATest",
      "created": "2013-12-10T06:54:48.222642",
      "webhook": null,
      "long_description": "AAAATest\n\n",
      "featured": false,
      "allow_anonymous_contributors": true,
      "published": true,
      "secret_key": "2ffgjngdf6bcbc38ba52561d4",
      "owner_id": 3738,
      "contacted": null,
      "id": 1069,
      "name": "AAAA Test"
    }

If a project is already unfeatured:

.. code-block:: python

    {
      "status_code": 415,
      "error": "Project.id 1069 is not featured"
    }

Help API
~~~~~~~~
**Endpoint: /help/api**

*Allowed methods*: **GET**

**GET**

Gives you the API help for your PYBOSSA

* **project_id**: a project id for the help example text. If no project exists it is null.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "project_id": 1104,
      "template": "help/privacy.html",
      "title": "API Help"
    }

Help privacy
~~~~~~~~~~~~
**Endpoint: /help/privacy**

*Allowed methods*: **GET**

**GET**

Gives you the privacy policy for your PYBOSSA

* **content**: Simplified HTML of rendered privacy policy.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "content": "<html><body><p>privacy policy here</p></body></html>"
      "template": "help/privacy.html",
      "title": "Privacy Policy"
    }

Help cookie policy
~~~~~~~~~~~~~~~~~~
**Endpoint: /help/cookies-policy**

*Allowed methods*: **GET**

**GET**

Gives you the cookie policy for your PYBOSSA

* **content**: Simplified HTML of rendered cookie policy.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "content": "<html><body><p>cookie policy here</p></body></html>"
      "template": "help/cookies_policy.html",
      "title": "Help: Cookies Policy"
    }

Help terms of use
~~~~~~~~~~~~~~~~~
**Endpoint: /help/terms-of-use**

*Allowed methods*: **GET**

**GET**

Gives you the terms of use for your PYBOSSA

* **content**: Simplified HTML of rendered terms of use.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "content": "<html><body><p>Terms of use text</p></body></html>"
      "template": "help/tos.html",
      "title": "Help: Terms of Use"
    }

PYBOSSA server stats
~~~~~~~~~~~~~~~~~~~~
**Endpoint: /stats/**

*Allowed methods*: **GET**

**GET**

Gives you the global stats of the PYBOSSA server.

* **title**: the title for the endpoint.
* **locs**: localizations for anonymous users that have contributed.
* **projects**: statistics about total published and draft projects.
* **show_locs**: if GEOIP is enabled to show that data.
* **stats**: Number of anonymous and authenticated users, number of draft and published projects, number of tasks, taskruns and total number of users.
* **tasks**: Task and Taskrun statistics.
* **tasks**: Task and Taskrun statistics.
* **top_5_projects_24_hours**: Top 5 projects in the last 24 hours.
* **top_5_users_24_hours**: Top 5 users in the last 24 hours.
* **users**: User statistics.

**Example output**

.. code-block:: python

    {
      "locs": "[]",
      "projects": {
        "label": "Projects Statistics",
        "values": [
          {
            "label": "Published",
            "value": [
              0,
              534
            ]
          },
          {
            "label": "Draft",
            "value": [
              0,
              1278
            ]
          }
        ]
      },
      "show_locs": false,
      "stats": {
        "n_anon": 27587,
        "n_auth": 11134,
        "n_draft_projects": 1278,
        "n_published_projects": 534,
        "n_task_runs": 1801222,
        "n_tasks": 553012,
        "n_total_projects": 1812,
        "n_total_users": 38721
      },
      "tasks": {
        "label": "Task and Task Run Statistics",
        "values": [
          {
            "label": "Tasks",
            "value": [
              0,
              553012
            ]
          },
          {
            "label": "Answers",
            "value": [
              1,
              1801222
            ]
          }
        ]
      },
      "template": "/stats/global.html",
      "title": "Global Statistics",
      "top5_projects_24_hours": [],
      "top5_users_24_hours": [],
      "users": {
        "label": "User Statistics",
        "values": [
          {
            "label": "Anonymous",
            "value": [
              0,
              27587
            ]
          },
          {
            "label": "Authenticated",
            "value": [
              0,
              11134
            ]
          }
        ]
      }
    }


Project Category Featured
~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/category/featured/**

*Allowed methods*: **GET**

**GET**

Gives you the list of featured projects.

* **pagination**: A pagination object for getting new featured projets from this category.
* **active_cat**: Active category.
* **projects**: List of projects belonging to this category.
* **categories**: List of available categories in this server.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "active_cat": {
        "created": null,
        "description": "Featured projects",
        "id": null,
        "name": "Featured",
        "short_name": "featured"
      },
      "categories": [
        {
          "created": null,
          "description": "Featured projects",
          "id": null,
          "name": "Featured",
          "short_name": "featured"
        },
        {
          "created": null,
          "description": "Social projects",
          "id": 2,
          "name": "Social",
          "short_name": "social"
        },
        {
          "created": "2013-06-18T11:13:44.789149",
          "description": "Art projects",
          "id": 3,
          "name": "Art",
          "short_name": "art"
        },
      ],
      "pagination": {
        "next": false,
        "page": 1,
        "per_page": 20,
        "prev": false,
        "total": 1
      },
      "projects": [
        {
          "created": "2014-02-22T15:09:23.691811",
          "description": "Image pattern recognition",
          "id": 1377,
          "info": {
            "container": "7",
            "thumbnail": "58.png"
          },
          "last_activity": "2 weeks ago",
          "last_activity_raw": "2017-01-31T09:18:28.450391",
          "n_tasks": 169671,
          "n_volunteers": 17499,
          "name": "Name",
          "overall_progress": 80,
          "owner": "John Doe",
          "short_name": "name",
          "updated": "2017-01-31T09:18:28.491496"
        },
      ],
      "template": "/projects/index.html",
      "title": "Projects"
    }

Project Category Draft
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/category/draft/**

*Allowed methods*: **GET**

**GET**

Gives you the list of featured projects.

* **pagination**: A pagination object for getting new draft projets from this category.
* **active_cat**: Active category.
* **projects**: List of projects belonging to this category.
* **categories**: List of available categories in this server.
* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "active_cat": {
        "created": null,
        "description": "Draft projects",
        "id": null,
        "name": "Draft",
        "short_name": "draft"
      },
      "categories": [
        {
          "created": null,
          "description": "Draft projects",
          "id": null,
          "name": "Draft",
          "short_name": "draft"
        },
        {
          "created": null,
          "description": "Social projects",
          "id": 2,
          "name": "Social",
          "short_name": "social"
        },
        {
          "created": "2013-06-18T11:13:44.789149",
          "description": "Art projects",
          "id": 3,
          "name": "Art",
          "short_name": "art"
        },
      ],
      "pagination": {
        "next": false,
        "page": 1,
        "per_page": 20,
        "prev": false,
        "total": 1
      },
      "projects": [
        {
          "created": "2014-02-22T15:09:23.691811",
          "description": "Draft 1",
          "id": 17,
          "info": {
            "container": "7",
            "thumbnail": "58.png"
          },
          "last_activity": "2 weeks ago",
          "last_activity_raw": "2017-01-31T09:18:28.450391",
          "n_tasks": 0,
          "n_volunteers": 0,
          "name": "Name",
          "overall_progress": 0,
          "owner": "John Doe",
          "short_name": "name",
          "updated": "2017-01-31T09:18:28.491496"
        },
      ],
      "template": "/projects/index.html",
      "title": "Projects"
    }

Project Creation
~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/new**

*Allowed methods*: **GET/POST**

**GET**

Gives you the list of required fields in the form to create a project.

* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.
* **form**: The form fields that need to be sent for creating the project. It contains the CSRF token for validating the POST, as well as an errors field in case that something is wrong.



**Example output**

.. code-block:: python

    {
      "errors": false,
      "form": {
        "csrf": "token",
        "description": null,
        "errors": {},
        "long_description": null,
        "name": null,
        "short_name": null
      },
      "template": "projects/new.html",
      "title": "Create a Project"
    }

Project Blog list
~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/blog**

*Allowed methods*: **GET**

**GET**

Gives you the list of posted blogs by the given project short name.

* **blogposts**: All the blog posts for the given project.
* **project**: Info about the project.


The project and owner fields will have more information if the onwer of the project does the request, providing its private information like api_key, password keys, etc. Otherwise it will be removed and only show public info.

**Example public output**

.. code-block:: python

    {
      "blogposts": [
        {
          "body": "Please, e-mail us to alejasan 4t ucm dot es if you find any bug. Thanks.",
          "created": "2014-05-14T14:25:04.899079",
          "id": 1,
          "project_id": 1377,
          "title": "We are working on the Alpha version.",
          "user_id": 3927
        },
      ],
      "n_completed_tasks": 137051,
      "n_task_runs": 1070561,
      "n_tasks": 169671,
      "n_volunteers": 17499,
      "overall_progress": 80,
      "owner": {
        "created": "2014-02-13T15:28:08.420187",
        "fullname": "John Doe",
        "info": {
          "avatar": "avatar.png",
          "container": "container"
        },
        "n_answers": 32814,
        "name": "johndoe",
        "rank": 4,
        "registered_ago": "3 years ago",
        "score": 32814
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "created": "2014-02-22T15:09:23.691811",
        "description": "Image pattern recognition",
        "featured": true,
        "id": 1,
        "info": {
          "container": "container",
          "thumbnail": "58.png"
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "Dark Skies ISS",
        "overall_progress": null,
        "owner": null,
        "short_name": "darkskies",
        "updated": "2017-01-31T09:18:28.491496"
      },
      "template": "projects/blog.html"
    }

Project Task Presenter Editor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/tasks/taskpresentereditor**

*Allowed methods*: **GET/POST**

**GET**

This endpoint allows you to get the list of available templates for the current project. This will only happen
when the project has an empty template, otherwise it will load the template for you.

* **template**: The Jinja2 template that could be rendered.
* **title**: the title for the endpoint.
* **presenters**: List of available templates (in HTML format). The name of them without the '.html' will be the argument for the endpoint.
* **last_activit**: last activity of the project.
* **n_task_runs**: number of task runs.
* **n_tasks**: number of tasks.
* **n_volunteers**: number of volunteers.
* **owner**: information about the owner.
* **pro_features**: which pro features are enabled.
* **pro_features**: which pro features are enabled.
* **project**: info about the project.
* **status**: status of the flash message.
* **flash**: flash message.


**Example output**

.. code-block:: python

     {
      "flash": "<strong>Note</strong> You will need to upload the tasks using the<a href=\"/project/asdf123/tasks/import\"> CSV importer</a> or download the project bundle and run the <strong>createTasks.py</strong> script in your computer",
      "last_activity": null,
      "n_completed_tasks": 0,
      "n_task_runs": 0,
      "n_tasks": 0,
      "n_volunteers": 0,
      "overall_progress": 0,
      "owner": {
        "api_key": "key",
        "confirmation_email_sent": false,
        "created": "2016-09-15T11:30:42.660450",
        "email_addr": "prueba@prueba.com",
        "facebook_user_id": null,
        "fullname": "prueba de json",
        "google_user_id": null,
        "id": 12030,
        "info": {
          "avatar": "avatar.png",
          "container": "user"
        },
        "n_answers": 5,
        "name": "pruebaadfadfa",
        "rank": 4411,
        "registered_ago": "6 months ago",
        "score": 5,
        "total": 11134,
        "twitter_user_id": null,
        "valid_email": true
      },
      "presenters": [
        "projects/presenters/basic.html",
        "projects/presenters/image.html",
        "projects/presenters/sound.html",
        "projects/presenters/video.html",
        "projects/presenters/map.html",
        "projects/presenters/pdf.html"
      ],
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "allow_anonymous_contributors": true,
        "category_id": 4,
        "contacted": false,
        "contrib_button": "draft",
        "created": "2017-01-11T09:37:43.613007",
        "description": "adsf",
        "featured": false,
        "id": 3,
        "info": {
          "passwd_hash": null,
          "task_presenter": ""
        },
        "long_description": "adsf",
        "n_blogposts": 0,
        "n_results": 0,
        "name": "asdf1324",
        "owner_id": 12030,
        "published": false,
        "secret_key": "73aee9df-be47-4e4c-8192-3a8bf0ab5161",
        "short_name": "asdf123",
        "updated": "2017-03-15T13:20:48.022328",
        "webhook": ""
      },
      "status": "info",
      "template": "projects/task_presenter_options.html",
      "title": "Project: asdf1324 &middot; Task Presenter Editor"
    }

If you want to preload the template from one of the available prenters, you have to pass the following
argument: **?template=basic** for the basic or **?template=iamge** for the image template.

**Example output**

.. code-block:: python

     {
      "errors": false,
      "flash": "Your code will be <em>automagically</em> rendered in                       the <strong>preview section</strong>. Click in the                       preview button!",
      "form": {
        "csrf": "token",
        "editor": "<div class=\"row\">\n    <div class=\"col-md-12\">\n        <h1>Write here your HTML Task Presenter</h1>\n    </div>\n</div>\n<script type=\"text/javascript\">\n(function() {\n    // Your JavaScript code\n    pybossa.taskLoaded(function(task, deferred){\n        // When the task is loaded, do....\n    });\n\n    pybossa.presentTask(function(task, deferred){\n        // Present the current task to the user\n        // Load the task data into the HTML DOM\n    });\n\n    pybossa.run('asdf123');\n})();\n</script>",
        "errors": {},
        "id": 3
      },
      "last_activity": null,
      "n_completed_tasks": 0,
      "n_task_runs": 0,
      "n_tasks": 0,
      "n_volunteers": 0,
      "overall_progress": 0,
      "owner": {
        "api_key": "key",
        "confirmation_email_sent": false,
        "created": "2016-09-15T11:30:42.660450",
        "email_addr": "prueba@prueba.com",
        "facebook_user_id": null,
        "fullname": "prueba de json",
        "google_user_id": null,
        "id": 0,
        "info": {
          "avatar": "avatar.png",
          "container": "user"
        },
        "n_answers": 5,
        "name": "pruebaadfadfa",
        "rank": 4411,
        "registered_ago": "6 months ago",
        "score": 5,
        "total": 11134,
        "twitter_user_id": null,
        "valid_email": true
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "allow_anonymous_contributors": true,
        "category_id": 4,
        "contacted": false,
        "contrib_button": "draft",
        "created": "2017-01-11T09:37:43.613007",
        "description": "adsf",
        "featured": false,
        "id": 3,
        "info": {
          "passwd_hash": null,
          "task_presenter": ""
        },
        "long_description": "adsf",
        "n_blogposts": 0,
        "n_results": 0,
        "name": "asdf1324",
        "owner_id": 0,
        "published": false,
        "secret_key": "73aee9df-be47-4e4c-8192-3a8bf0ab5161",
        "short_name": "asdf123",
        "updated": "2017-03-15T13:20:48.022328",
        "webhook": ""
      },
      "status": "info",
      "template": "projects/task_presenter_editor.html",
      "title": "Project: asdf1324 &middot; Task Presenter Editor"
    }

Then, you can use that template, or if you prefer you can do a POST directly without that information. As in 
any other request involving a POST you will need the CSRFToken to validate it.

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken". You will have to POST the data fields found in the previous example,
as it contains the information about the fields: specifically **editor** with the HTML/CSS/JS that you want
to provide.

If the post is successfull, you will get the following output:

**Example output**

.. code-block:: python

    {
      "flash": "<i class=\"icon-ok\"></i> Task presenter added!",
      "next": "/project/asdf123/tasks/",
      "status": "success"
    }

Project Delete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/delete**

*Allowed methods*: **GET/POST**

**GET**

The GET endpoint allows you to get all the info about the project (see the Project endpoint as well) as well
as the csrf token. As this endpoint does not have any form, the csrf token is not inside the form field.

**Example output**

.. code-block:: python

    {
      "csrf": "token",
      "last_activity": null,
      "n_tasks": 0,
      "overall_progress": 0,
      "owner": {
        "api_key": "key",
        "confirmation_email_sent": false,
        "created": "2016-09-15T11:30:42.660450",
        "email_addr": "prueba@prueba.com",
        "facebook_user_id": null,
        "fullname": "prueba de json",
        "google_user_id": null,
        "id": 0,
        "info": {
          "avatar": "avatar.png",
          "container": "0"
        },
        "n_answers": 5,
        "name": "pruebaadfadfa",
        "rank": 4411,
        "registered_ago": "6 months ago",
        "score": 5,
        "total": 11134,
        "twitter_user_id": null,
        "valid_email": true
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "allow_anonymous_contributors": true,
        "category_id": 2,
        "contacted": false,
        "created": "2017-03-15T15:02:12.160810",
        "description": "asdf",
        "featured": false,
        "id": 3,
        "info": {},
        "long_description": "asdf",
        "name": "algo",
        "owner_id": 12030,
        "published": false,
        "secret_key": "c5a77943-f5a4-484a-86bb-d69559e80357",
        "short_name": "algo",
        "updated": "2017-03-15T15:02:12.160823",
        "webhook": null
      },
      "template": "/projects/delete.html",
      "title": "Project: algo &middot; Delete"
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

**Example output**

.. code-block:: python

    {
      "flash": "Project deleted!",
      "next": "/account/pruebaadfadfa/",
      "status": "success"
    }


Project update
~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/update**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **form**: the form fields that need to be sent for updating the project. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **upload_form**: the form fields that need to be sent for updating the project's avatar. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.

**Example output**

.. code-block:: python

    {
      "form": {
        "allow_anonymous_contributors": false,
        "category_id": 2,
        "csrf": "token",
        "description": "description",
        "errors": {},
        "id": 3117,
        "long_description": "long description",
        "name": "name",
        "password": null,
        "protect": false,
        "short_name": "slug",
        "webhook": null
      },
      "last_activity": null,
      "n_completed_tasks": 0,
      "n_task_runs": 0,
      "n_tasks": 2,
      "n_volunteers": 0,
      "overall_progress": 0,
      "owner": {
        "api_key": "key",
        "confirmation_email_sent": false,
        "created": "2012-06-06T06:27:18.760254",
        "email_addr": "email.com",
        "facebook_user_id": null,
        "fullname": "John Doe",
        "google_user_id": null,
        "id": 0,
        "info": {
          "avatar": "avatar.png",
          "container": "user",
          "twitter_token": {
            "oauth_token": "token",
            "oauth_token_secret": "token"
          }
        },
        "n_answers": 2414,
        "name": "johndoe",
        "rank": 69,
        "registered_ago": "4 years ago",
        "score": 2414,
        "total": 11134,
        "twitter_user_id": 12,
        "valid_email": false
      },
      "pro_features": {
        "auditlog_enabled": true,
        "autoimporter_enabled": true,
        "webhooks_enabled": true
      },
      "project": {
        "allow_anonymous_contributors": false,
        "category_id": 2,
        "contacted": false,
        "contrib_button": "can_contribute",
        "created": "2015-06-29T08:23:14.201331",
        "description": "description",
        "featured": false,
        "id": 0,
        "info": {
          "container": "user",
          "passwd_hash": null,
          "task_presenter": "HTML+CSS+JS,
          "thumbnail": "thumbnail.png"
        },
        "long_description": "long description",
        "n_blogposts": 0,
        "n_results": 0,
        "name": "name",
        "owner_id": 0,
        "published": true,
        "secret_key": "key",
        "short_name": "slug",
        "updated": "2017-03-16T14:50:45.055331",
        "webhook": null
      },
      "template": "/projects/update.html",
      "title": "Project: name &middot; Update",
      "upload_form": {
        "avatar": null,
        "csrf": "token",
        "errors": {},
        "id": null,
        "x1": 0,
        "x2": 0,
        "y1": 0,
        "y2": 0
      }
    }

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

As this endpoint supports **two** different forms, you must specify which form are
you targetting adding an extra key: **btn**. The options for this key are:

  **Upload**: to update the **upload_form**.

The other one does not need this extra key.

.. note::
    Be sure to respect the Uppercase in the first letter, otherwise it will fail.

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.
* **form**: the form fields with the sent information. It contains the csrf token for validating the post, as well as an errors field in case that something is wrong.

**Example output**

.. code-block:: python

    {
      "flash": "Your profile has been updated!",
      "next": "/account/pruebaadfadfa/update",
      "status": "success"
    }


If there's an error in the form fields, you will get them in the **form.errors** key:

.. code-block:: python

    {
      "flash": "Please correct the errors",
      "form": {
        "allow_anonymous_contributors": false,
        "category_id": 2,
        "csrf": "token",
        "description": "description",
        "errors": {
          "short_name": [
            "This field is required."
          ]
        },
        "id": 3117,
        "long_description": "new description",
        "name": "new name",
        "password": null,
        "protect": true,
        "short_name": "",
        "webhook": null
      },
      ...
    }

.. note::
    For updating the avatar is very important to not set the *Content-Type*. If you
    are using jQuery, set it to False, so the file is handled properly.

    The (x1,x2,y1,y2) are the coordinates for cutting the image and create the avatar.

    (x1,y1) are the offset left of the cropped area and  the offset top of the cropped
    area respectively; and (x2,y2) are the width and height of the crop. And don't forget
    to add an extra key to the form-data: 'btn' with a value Upload to select this form.

Project reset secret key
~~~~~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/resetsecretkey**

*Allowed methods*: **POST**

Resets the secret key of a project.

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken" retrieved from the GET endpont **/project/<short_name>/update**.

**Example output**

.. code-block:: python

    {
      "flash": "New secret key generated",
      "next": "/project/flickrproject2/update",
      "status": "success"
    }

Project tasks browse
~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/tasks/browse/**
**Endpoint: /project/<short_name>/tasks/browse/<int:page>**

*Allowed methods*: **GET**

* **n_completed_tasks**: number of completed tasks
* **n_tasks**: number of tasks
* **n_volunteers**: number of volunteers
* **overall_progress**: overall progress
* **owner**: project owner
* **pagination**: pagination information
* **pro_features**: pro features enabled or not
* **project**: project information
* **tasks**: tasks, paginated
* **template**: the Jinja2 template that should be rendered in case of text/html.
* **title**: the title for the endpoint.

**Example output**

.. code-block:: python

    {
      "n_completed_tasks": 0,
      "n_tasks": 1,
      "n_volunteers": 0,
      "overall_progress": 0,
      "owner": {
        "created": "2017-04-17T23:56:22.892222",
        "fullname": "John Doe",
        "info": {},
        "locale": null,
        "n_answers": 0,
        "name": "johndoe",
        "rank": null,
        "registered_ago": "3 hours ago",
        "score": null
      },
      "pagination": {
        "next": false,
        "page": 1,
        "per_page": 10,
        "prev": false,
        "total": 1
      },
      "pro_features": {
        "auditlog_enabled": false,
        "autoimporter_enabled": false,
        "webhooks_enabled": false
      },
      "project": {
        "created": "2017-04-17T23:56:23.416754",
        "description": "Description",
        "featured": false,
        "id": 1,
        "info": {},
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "Sample Project",
        "overall_progress": null,
        "owner": null,
        "short_name": "sampleapp",
        "updated": "2017-04-17T23:56:23.589652"
      },
      "tasks": [
        {
          "id": 1,
          "n_answers": 10,
          "n_task_runs": 0,
          "pct_status": 0.0
        }
      ],
      "template": "/projects/tasks_browse.html",
      "title": "Project: Sample Project &middot; Tasks"
    }

Project tasks import
~~~~~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/tasks/import**

*Allowed methods*: **GET/POST**

**GET**

It returns a JSON object with the following information:

* **available_importers**: A list of available importers for the server. To use one of the items, you have to add to the endpoint the following argument: *?type=name* where name is the string that you will find in the list of importers in the format: *projects/tasks/name.html*.
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.

**Example output**

.. code-block:: python

    {
      "available_importers": [
        "projects/tasks/epicollect.html",
        "projects/tasks/csv.html",
        "projects/tasks/s3.html",
        "projects/tasks/twitter.html",
        "projects/tasks/youtube.html",
        "projects/tasks/gdocs.html",
        "projects/tasks/dropbox.html",
        "projects/tasks/flickr.html"
      ],
      "form": null,
      "loading_text": "Importing tasks, this may take a while, wait...",
      "n_completed_tasks": 0,
      "n_tasks": 5,
      "n_volunteers": 0,
      "overall_progress": 0,
      "owner": {
        "api_key": "key",
        "confirmation_email_sent": false,
        "created": "2012-06-06T06:27:18.760254",
        "email_addr": "johndoe@gmail.com",
        "facebook_user_id": null,
        "fullname": "John Doe",
        "google_user_id": null,
        "id": 0,
        "info": {
          "avatar": "avatar.png",
          "container": "user",
          "twitter_token": {
            "oauth_token": "",
            "oauth_token_secret": ""
          }
        },
        "n_answers": 2414,
        "name": "johndoe",
        "rank": 69,
        "registered_ago": "4 years ago",
        "score": 2414,
        "total": 11134,
        "twitter_user_id": 12,
        "valid_email": false
      },
      "pro_features": {
        "auditlog_enabled": true,
        "autoimporter_enabled": true,
        "webhooks_enabled": true
      },
      "project": {
        "allow_anonymous_contributors": false,
        "category_id": 2,
        "contacted": false,
        "contrib_button": "can_contribute",
        "created": "2015-06-29T08:23:14.201331",
        "description": "old",
        "featured": false,
        "id": 3117,
        "info": {
          "container": "user",
          "passwd_hash": null,
          "task_presenter": "HTML+CSS+JS"
          "thumbnail": "avatar.png"
        },
        "long_description": "algo",
        "n_blogposts": 0,
        "n_results": 0,
        "name": "name",
        "owner_id": 3,
        "published": true,
        "secret_key": "f",
        "short_name": "name",
        "updated": "2017-03-17T09:15:46.867215",
        "webhook": null
      },
      "target": "project.import_task",
      "task_tmpls": [
        "projects/tasks/gdocs-sound.html",
        "projects/tasks/gdocs-map.html",
        "projects/tasks/gdocs-image.html",
        "projects/tasks/gdocs-video.html",
        "projects/tasks/gdocs-pdf.html"
      ],
      "template": "/projects/task_import_options.html",
      "title": "Project: bevan &middot; Import Tasks"
    }

Therefore, if you want to import tasks from a CSV link, you will have to do the following GET::

    GET server/project/<short_name>/tasks/import?type=csv

That query will return the same output as before, but instead of the available_importers, you will get the the form fields and CSRF token for that importer. 

**POST**

To send a valid POST request you need to pass the *csrf token* in the headers. Use
the following header: "X-CSRFToken".

It returns a JSON object with the following information:

* **flash**: A success message, or error indicating if the request was succesful.

**Example output**

.. code-block:: python

    {
      "flash": "Tasks imported",
      "next": "/project/<short_name>/tasks/",
      "status": "success"
    }

Project tutorial
~~~~~~~~~~~~~~~~
**Endpoint: /project/<short_name>/tutorial**

**GET**

It returns a JSON object with the following information:

* **owner**: owner information
* **project**: project information
* **template**: The Jinja2 template that could be rendered.
* **title**: The title for the view.

**Example output**

.. code-block:: python

    {
      "owner": {
        "created": "2014-02-13T15:28:08.420187",
        "fullname": "John Doe",
        "info": {
          "avatar": "1410769844.15_avatar.png",
          "avatar_url": null,
          "container": "user_3927",
          "extra": null
        },
        "locale": null,
        "n_answers": 43565,
        "name": "jdoe",
        "rank": 3,
        "registered_ago": "3 years ago",
        "score": 43565
      },
      "project": {
        "created": "2014-02-22T15:09:23.691811",
        "description": "Image pattern recognition",
        "featured": true,
        "id": 1377,
        "info": {
          "container": "user_3927",
          "thumbnail": "app_1377_thumbnail_1410772569.58.png",
          "thumbnail_url": null
        },
        "last_activity": null,
        "last_activity_raw": null,
        "n_tasks": null,
        "n_volunteers": null,
        "name": "myproject",
        "overall_progress": null,
        "owner": null,
        "short_name": "johndoeproject",
        "updated": "2017-03-02T21:00:33.965587"
      },
      "template": "/projects/tutorial.html",
      "title": "Project: myproject"
    }
