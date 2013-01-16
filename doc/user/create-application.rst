====================================
Creating an Application
====================================

Readers may wish to start with the :doc:`Step by step tutorial on creating an
Application <create-application-tutorial>` which walks through creating a
simple photo classification application.

1. Creating the Application itself
==================================

First of all we have to create an application for the project. An application
represents a set of tasks that have to be resolved by people, so an application
will have the following items:

    1. **Name**,
    2. **Short name** or **slug**,
    3. **Description** and
    4. **Task Presenter**

The **slug** or **short name** is a shortcut for accessing the application via
the web (short urls like this http://domain.com/app/slug).

The **description** is the question that the volunteers will have to solve.
Thus, it should be a direct question like: Do you see a human in this photo?

Finally, the **task presenter**. This field contains the HTML and JS that your
application will be using to present the tasks to the users and save the
answers in the server.

In the following following sub-sections there is an explanation of the two
available methods to create an application:

    1. via the web interface, or
    2. via the API.


Via the Web Interface
---------------------

Creating an application using the web interface involves three steps:

    1. Create the application
    2. Import the tasks using a CSV file
    3. Create the task presenter for the users

Creating the application
~~~~~~~~~~~~~~~~~~~~~~~~

In order to create an application in PyBossa via the web interface you have to:

    1. Sign in into your PyBossa server (or create an account).
    2. Click in **create** link of the top bar and click again in the button
       named: **Or using a web form and a CSV file importer for the tasks**.
    3. After clicking in the previous button, you will have to fill in a form
       with the following information:
         1. **Name**: the full name of your application, i.e. Flickr Person
            Finder
         2. **Short Name**: the *slug* or short name used in the URL for
            accessing your application, i.e. *flickrperson*.
         3. **Description**: A **short** description of the application, i.e.
            *Image pattern recognition*.
         4. **Long Description**: A *long* description where you can use HTML
            to format the description of your application. This field is
            usually used to provide information about the application, the
            developer, the researcher group or institutions involved in the
            application, etc.
         5. **Hide**: Click in this field if you want to hide the application.
    4. Once you have filled all the fields, click in the **Create the
       application** button, and you will have created your first application.

Once you have created the application, you should be able to see it in your
profile page.

Importing the tasks via the CSV file importer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tasks can be imported from a CSV file or a Google Spreadsheet via the bulk
importer. You have to do the following:

    1. Navigate to your application's page.
    2. Click on **Import Tasks**, right next to **Edit the Application**.
    3. Provide a URL to a Google Docs Spreadsheet or a CSV file.  If you're
       trying to import from a Google Spreadsheet, ensure the file is
       accessible to everyone with link or is public.

.. note::

   Your spreadsheet/CSV file must contain a header row. All the fields in the
   CSV will be    serialized to JSON and stored in the **info** field. If
   your field name is one of **state**, **quorum**, **calibration**,
   **priority_0**, or **n_answers**, it will be saved in the respective
   columns. Your spreadsheet must be visible to public or everyone with URL.

Creating the Task Presenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the application and the tasks in the server, you can start
working with the Task Presenter, which will be the application that will get
the tasks of your application, present them to the volunteer and save the
answers provided by the users.

If you have followed all the steps described in this section, you will be
already in the page of your application, however, if you are not, you only need
to access your application URL to work with your application. If your application
*slug* or *short name* is *flickrperson* you will be able to access the
application managing options in this URL::

    http://PYBOSSA-SERVER/app/flickrperson

.. note::
    
    You need to be logged in, otherwise you will not be able to modify the
    application.

Another way for accessing your application (or applications) is clicking in
your user name and select the *Account* item from the drop down menu, and then 
click in the left bar: **My Applications** Published or Draft ones. From there
you will be able to manage your applications.

Once you have chosen your application, you can add the task presenter by
clicking in the button named **Edit the task presenter**. 

After clicking in this button, a new web page will be shown where you can
basically type the code required for getting the tasks and load them into a DOM
that you will create.

We recommend to read the 
:doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`, as you will understand
how to create the task presenter, which is basically adding some HTML skeleton
to load the task data, input fields to get the answer of the users, and some
JavaScript to make it to work.


Via the API
-----------
Creating an application using the API involves also three steps:

    1. Create the application
    2. Create the tasks 
    3. Create the task presenter for the users

Creating the application
~~~~~~~~~~~~~~~~~~~~~~~~

You can create an application via the API URL **/api/app** with a POST request.

You have to provide the following information about the application and convert
it to a JSON object (the actual values are taken from the `Flickr Person demo
application <http://app-flickrperson.rtfd.org>`_)::

  name = u'Flickr Person Finder'
  short_name = u'FlickrPerson'
  description = u'Do you see a human in this photo?'
  info = { 'thumbnail': u'http://domain/thumbnail.png',
           'task_presenter': u'<div> Skeleton for the tasks</div>' }
  data = dict(name = name, short_name = short_name, description = description, info = info, hidden = 0)
  data = json.dumps(data)


Flickr Person Finder, which is a **demo template** that **you can re-use**
to create your own application, simplifies this step by using a simple
file named **app.json**:

.. code-block:: javascript

    {
        "name": "Flickr Person Finder",
        "short_name": "flickrperson",
        "thumbnail": "http://imageshack.us/a/img37/156/flickrpersonthumbnail.png",
        "description": "Image pattern recognition",
        "question": "Do you see a human in this photo?"
    }


As Flickr Person is trying to figure out if there is a person in
the photo, the question is: *Do you see a human in this photo?*. The file
provides a basic configuration for your application, where you can even specify
the icon thumbnail for your application.

The **Thumbnail** is a field that you can use to include a nice icon for the
application. Flickr Person Finder uses as a thumbnail a cropped version
(100x100 pixels) of a `Flickr photo from Sean McGrath (license CC BY 2.0)
<http://www.flickr.com/photos/mcgraths/3289448299/>`_. If you decide to not
include a thumbnail, PyBossa will render for you a place holder
icon of 100x100 pixels.

Creating the tasks
~~~~~~~~~~~~~~~~~~

As in all the previous step, we are going to create a JSON
object and POST it using the following API URL **/api/task** in order to add
tasks to an application that you own. 

For PyBossa all the tasks are JSON objects with a field named **info** where
the owners of the application can add any JSON object that will represent
a task for their application. For example, using again the `Flickr Person demo application
<http://app-flickrperson.rtfd.org>`_ example, we need to create a JSON object
that should have the link to the photo that we want to identify:

.. code-block:: python

    info = dict (link = photo['link'], url = photo['url_m'])
    data = dict (app_id=app_id,
                 state=0,
                 info=info,
                 calibration=0,
                 priority_0=0)
    data = json.dumps(data)

The most important field for the task is the **info** one. This field will be
used to store a JSON object with the required data for the task. As  `Flickr Person
<http://app-flickrperson.rtfd.org>`_ is trying to figure out if there is a human or
not in a photo, the provided information is:

    1. the Flickr web page posting the photo, and
    2. the direct URL to the image, the <img src> value.

The **info** field is a free-form field that can be populated with any
structure. If your application needs more fields, you can add them and use the
format that best fits your needs.

.. note::

    **The API request has to be authenticated and authorized**.
    You can get an API-KEY creating an account in the
    server, and checking the API-KEY created for your user, check the profile
    account (click in your user name) and copy the field **API-KEY**.

    This API-KEY should be passed as a POST argument like this with the
    previous data:

    [POST] http://domain/api/task/?api_key=API-KEY


One of the benefits of using the API is that you can create tasks polling other
web services like Flickr, where you can basically use an API. Once we have
created the tasks, we will need to create the task presenter for the
application.


Creating the Task Presenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **Task Presenter** is usually a template of HTML+JS that will present the
tasks to the users, and save the answers in the database. The `Flickr Person demo
application <http://app-flickrperson.rtfd.org>`_ provides a simple template
which has a <div> to load the input files, in this case the photo, and another
<div> to load the action buttons that the users will be able to to press to
answer the question and save it in the database. Please, check the `Flickr Person demo
application documentation <http://app-flickrperson.rtfd.org>`_ for more details
about the **task presenter**.

As we will be using the API for creating the task presenter, we will basically
have to create an HTML file, read it, and post it into PyBossa using the API.
Once the presenter has been posted to the application, you can edit it locally
with your own editor, or using the PyBossa interface (see previous section).

.. note::

    **The API request has to be authenticated and authorized**.
    You can get an API-KEY creating an account in the
    server, and checking the API-KEY created for your user, check the profile
    account (click in your user name) and copy the field **API-KEY**.

    This API-KEY should be passed as a POST argument like this with the
    previous data:

    [POST] http://domain/api/app/?api_key=API-KEY

We recommend to read the 
:doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`, as you will understand
how to create the task presenter, which is basically adding some HTML skeleton
to load the task data, input fields to get the answer of the users, and some
JavaScript to make it to work.


2. Step by step tutorial on creating an application
===================================================

If you want to learn more about the whole process of creating an application,
please, see the detailed example of creating an application in the
:doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`.

