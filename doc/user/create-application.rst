====================================
Creating a Crowdsourcing Application
====================================

Readers may wish to start with the :doc:`Step by step tutorial on creating an
Application <create-application-tutorial>` which walks through creating a
simple photo classification App.

1. Create the Application itself
================================

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

In order to create an application in PyBossa via the web interface you have to:

    1. Log in into your PyBossa server (or create an account).
    2. Click in your user name, and check the **Applications** left menu list.
    3. Click the blue button **Create a new application** and fill in the
       form.
    4. Provide a *name, short name* or slug for the application and use the
       *description* field to right the question that you want to ask to the
       volunteers.
    5. The *hide* option allows you to hide the application from the application
       list of the server.

Once you have created the application, you should be able to see it in your
profile page.

This step will not create the **Task Presenter** for the application, so you
will have to use the API to update the application or create it directly using
the API.

Via the API
-----------

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

The **description** field is used to store the **question** that we want to ask
in our tasks. As Flickr Person is trying to figure out if there is a person in
the photo, the question is: *Do you see a human in this photo?*. The other two
fields are the names used for naming the application (short_name will be the
slug name of the application). Finally, the *hidden* field is a bool flag to hide the
application for users but not for the creator.

The **Thumbnail** is a field that you can use to include a nice icon for the
application. Flickr Person Finder uses as a thumbnail a cropped version
(100x100 pixels) of a `Flickr photo from Sean McGrath (license CC BY 2.0)
<http://www.flickr.com/photos/mcgraths/3289448299/>`_. If you decide to not
include a thumbnail, PyBossa will render for you a grey icon of 100x100 pixels.

The **Task Presenter** is usually a template of HTML+JS that will present the
tasks to the users, and save the answers in the database. The `Flickr Person demo
application <http://app-flickrperson.rtfd.org>`_ provides a simple template
which has a <div> to load the input files, in this case the photo, and another
<div> to load the action buttons that the users will be able to to press to
answer the question and save it in the database. Please, check the `Flickr Person demo
application documentation <http://app-flickrperson.rtfd.org>`_ for more details
about the **task presenter**.

.. note::

    **The API request has to be authenticated and authorized**.
    You can get an API-KEY creating an account in the
    server, and checking the API-KEY created for your user, check the profile
    account (click in your user name) and copy the field **API-KEY**.

    This API-KEY should be passed as a POST argument like this with the
    previous data:

    [POST] http://domain/api/app/?api_key=API-KEY


3. Create the Tasks
===================

Via the Web Interface
---------------------
Tasks can be imported from a CSV file or a Google Spreadsheet via the bulk
importer. You have to do the following:

    1. Navigate to your application's page.
    2. Click on **Import Tasks**, right next to **Edit the Application**.
    3. Provide a URL to the CSV file.  If you're trying to import from a
       Google Spreadsheet, add **&output=csv** to the end of the URL and
       ensure the file is accessible to everyone with link or is public.

.. note::

   Your CSV file must contain a header row. All the fields in the CSV will be
   serialized to json and stored in the **info** field. If your field name is
   one of **state**, **quorum**, **calibration**, **priority_0**, or
   **n_answers**, it will be saved in the respective columns. Your spreadsheet
   must be visible to public or everyone with URL.

Via the API
-----------
The last step involves the creation of a set of tasks associated to an
**application**. As in all the previous steps, we are going to create a JSON
object and POST it using the following API URL **/api/task**. For instance,
following with the `Flickr Person demo application
<http://app-flickrperson.rtfd.org>`_ example, the JSON object will be like
this::

  info = dict (link = photo['link'], url = photo['url_m'])
  data = dict (app_id = app_id, state = 0, info = info, calibration = 0, priority_0 = 0)
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


4. Step by step tutorial on creating an application
===================================================

If you want to learn more about the whole process of creating an application,
please, see the detailed example of creating an application in the
:doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`.

