
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


Finally you can also get the results ordered by date of creation listing first the latest
domain objects (projects, tasks, task runs and results) using the following argument
in the URL::

    GET http://server.com/api/project?desc=true


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
by PYBOSSA (currently Twitter, Facebook and Google) can request his own oAuth
tokens by doing::

    GET http://{pybossa-site-url}/api/token?api_key=API-KEY

Additionally, the user can specify any of the tokens if only its retrieval is
desired::

    GET http://{pybossa-site-url}/api/token/{provider}?api_key=API-KEY

Where 'provider' will be any of the third parties supported, i.e. 'twitter',
'facebook' or 'google'.

Using your own user database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    POST http://{pybossa-site-url}/api/taskrun


.. note::
    The TaskRun object needs to have the external_uid field filled with 1xa. 

As simple as that! 


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

If you are not logged in you will get this output:

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
