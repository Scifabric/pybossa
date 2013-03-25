=============================================
Quick overview: Creating your own Application
=============================================

This is a short guide about how you can create an application in a PyBossa
server. Readers may wish to start with the :doc:`Step by step tutorial on creating an
Application <tutorial>` which walks through creating a
simple photo classification application if they want to understand all the
details about how you create an application.

First of all we have to create an application for the project. An application
represents a set of tasks that have to be resolved by people, so an application
will have the following items:

    1. **Name**,
    2. **Short name** or **slug**, and
    3. **Description** and

The **slug** or **short name** is a shortcut for accessing the application via
the web (short urls like this http://domain.com/app/slug).

The **description** is a short sentence that will be used to describe your
application.

An application can be created using two different methods:

* :ref:`web-interface`, or
* :ref:`api-interface`.


.. _web-interface:

Using the Web Interface
=======================

Creating an application using the web interface involves three steps:

    1. Create the application,
    2. Import the tasks using the *simple built-in* :ref:`task-creator` 
       (uploading a CSV file or Google Spreadsheet link exported
       as CSV), and
    3. Write the :ref:`task-presenter` for the users.

Creating the application
~~~~~~~~~~~~~~~~~~~~~~~~

In order to create an application in PyBossa via the web interface you have to:

1. Sign in into your PyBossa server (or create an account)

.. image:: http://i.imgur.com/WQuEVqL.png
   :alt: PyBossa sign in
   :width: 100%

PyBossa supports Twitter, Facebook and Google sign in methods, or if you prefer
you can create your account within the PyBossa server. Check the following
figure:

.. image:: http://i.imgur.com/g4mFENC.png
    :alt: PyBossa sign in methods

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
     4. **Icon Link**: A URL with the icon that you want to use in your
        application.
     5. **Allow Anonymous Contributors**: By default anonymous and
        authenticated users can participate in all the applications, however
        you can change it to only allow authenticated volunteers to
        participate. 
     6. **Task Scheduler**: The task scheduler is in charge in distributing the
        tasks within the volunteers crowd. By default, the system will send the
        same task to all the users until a minimum of 30 answers are obtained
        for each task, then it will start sending the next task of your
        application. You can change it to **breadth first** if you want to send
        to every user a different task every time.
     4. **Long Description**: A *long* description where you can use HTML
        to format the description of your application. This field is
        usually used to provide information about the application, the
        developer, the researcher group or institutions involved in the
        application, etc.
     5. **Hide**: Click in this field if you want to hide the application.

.. image:: http://i.imgur.com/MdNRUnK.png
    :alt: PyBossa Create link

4. Once you have filled all the fields, click in the **Create the
   application** button, and you will have created your first application.

Once you have created the application, you should will be redirected to the
**settings** application page:

.. image:: http://i.imgur.com/AeBAy7q.png

Importing the tasks via the built-in CSV Task Creator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tasks can be imported from a CSV file or a Google Spreadsheet via the simple
built-in :ref:`task-creator`. You have to do the following:

1. Navigate to your application's page (you can directly access it using 
   the *slug* application name: http://server/app/slug).

.. image:: http://i.imgur.com/98o4ixD.png

2. Click in the **Settings** section -on the left side local navigation menu:

.. image:: http://i.imgur.com/AeBAy7q.png
    
3. Scroll down a bit to the **Task Settings** and  click on the **Import Tasks** 
   button. After clicking on it you will see 6 different options:

.. image:: http://i.imgur.com/wyGxV4s.png

The **Basic** template, allows you to upload your own CSV file:

.. image:: http://i.imgur.com/aU0A9gL.png

4. Where you will have to provide a URL to a Google Docs Spreadsheet or a CSV file.  If you're
   trying to import from a Google Spreadsheet, ensure the file is
   accessible to everyone with link or is public.

.. note::

   Your spreadsheet/CSV file must contain a header row. All the fields in the
   CSV will be serialized to JSON and stored in the **info** field. If
   your field name is one of **state**, **quorum**, **calibration**,
   **priority_0**, or **n_answers**, it will be saved in the respective
   columns. Your spreadsheet must be visible to public or everyone with URL.

The other three options provide a Google Docs URL to a public spreadsheet, 
that you can automatically import for your application (the URL will
automatically copy and pasted into the input field for importing the tasks). 
By using these templates, you'll be able to learn the structure of the tasks,
and directly re-use the :ref:`task-presenter` templates that know the structure
(name of the columns) for presenting the task. 

Additionally, you can re-use the templates by downloading the CSV files from
Google Docs, or even copying them to your own Google Drive account (click in
*File* -> *Make a copy* in the Google Doc Spreadsheet). The
available templates are the following:

* `Image Pattern Recognition`_
* `Sound Pattern Recognition`_
* `Geo-coding`_ and
* `PDF transcription`_. 

.. note::

    You can also upload your own CSV files to free web hosting services like
    DropBox_ or `Ubuntu One`_. You will only need to copy the file to the
    **public** folder of the chosen service in your own computer
    (i.e. DropbBox Public folder) and then copy the public link created by the 
    service. Once you have the public link, all you need in order to import the 
    tasks is to paste it in the input box of the section **From a CSV file**.


.. _`Image Pattern Recognition`: https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE&usp=sharing#gid=0
.. _`Sound Pattern Recognition`: https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc#gid=0
.. _`Geo-coding`: https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc&usp=sharing
.. _`PDF transcription`: https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE&usp=sharing
.. _`DropBox`: http://www.dropbox.com
.. _`Ubuntu One`: http://one.ubuntu.com


Importing the tasks from an EpiCollect Plus Public Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EpiCollect_ provides a web application for the generation of forms and freely hosted
project websites (using Google's AppEngine) for many kinds of mobile data 
collection projects.

Data can be collected using multiple mobile phones running either the Android 
Operating system or the iPhone (using the EpiCollect mobile app) and all data can 
be synchronised from the phones and viewed centrally (using Google Maps) via the 
Project website or directly on the phones.

EpiCollect_ can help you to recollect data samples according to a form that
could include multimedia like photos. Moreover, EpiCollect_ can geolocate the data 
sample as it supports the built-in GPS that all modern smartphones have. 

For example, you can create
an EpiCollect_ project where the form will ask the user to take a picture of
a lake, geo-locate it automatically via the smartphone built-in GPS and upload
the picture to the EpiCollect_ server. If the user does not have Internet
access at that moment, the user will be able to synchronize the data afterwards
i.e. when the user has access to an Internet WIFI hotspot.

PyBossa can automatically import data from a public EpiCollect_ Plus project
that you own or that it is publicly available in the EpiCollect_ web site and
help you to validate, analyze, etc. the data that have been obtained via
EpiCollect.

If you want to import the data points submitted to a **public** EpiCollect_
project, you will have to follow the next steps:

1. Navigate to your application's page (you can directly access it using 
   the *slug* application name: http://server/app/slug).

.. image:: http://i.imgur.com/98o4ixD.png

2. Click in the **Settings** section -on the left side local navigation menu:

.. image:: http://i.imgur.com/AeBAy7q.png
    
3. Scroll down a bit to the **Task Settings** and  click on the **Import Tasks** 
   button. After clicking on it you will see 6 different options:

.. image:: http://i.imgur.com/wyGxV4s.png

4. Click in the second one: **Use an EpiCollect Project**

5. Then, type the **name of the EpiCollect project** and the name of the
   **form** that you want to import, and click in the import button

.. image:: http://i.imgur.com/bCuTtl0.png

All the data points should be imported now in your application.

.. _`EpiCollect`: http://plus.epicollect.net

Flushing all the tasks
~~~~~~~~~~~~~~~~~~~~~~

The application settings gives you an option to automatically **delete all the
tasks and associated task runs** from your application.

.. note::
    **This action cannot be un-done, so please, be sure that you want to actually
    delete all the tasks.**

If you are sure that you want to flush all the tasks and task runs for your
application, go to the application page (http://server/app/slug/) and click in
the **Settings** option of the left local navigation menu:

.. image:: http://i.imgur.com/AeBAy7q.png

Then, you will see that there is a sub section called: **Task Settings** and
a button with the label: **Delete the tasks**. Click in that button and a new
page will be shown:

.. image:: http://i.imgur.com/EKs3wE3.png
    :width:100%

As you can see, a **red warning alert** is shown, warning you that if you click
in the **yes** button, you will be deleting not only the application tasks, but
also the answers (task runs) that you have recollected for your application. Be
sure before proceeding that you want to delete all the tasks. After clicking in
the **yes** button, you will see that all the tasks have been flushed.

Creating the Task Presenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the application and the tasks in the server, you can start
working with the :ref:`task-presenter`, which will be the web application that 
will get the tasks of your application, present them to the volunteer and save the
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
your *user name* and select the *My Applications* item from the drop down menu.
From there you will be able to manage your applications:

.. image:: http://i.imgur.com/nH9u2nk.png
    :alt: PyBossa User Account

.. image:: http://i.imgur.com/abu0SsT.png
    :width: 100%

Once you have chosen your application, you can add :ref:`task-presenter` by
clicking in the **Settings** local navigation link, and then under the sub
section *Application Settings* click in the button named **Edit the task presenter**. 

.. image:: http://i.imgur.com/AeBAy7q.png

After clicking in this button, a new web page will be shown where you can
choose a template to start coding your application, so you don't have to
actually start from scratch. 

.. image:: http://i.imgur.com/Xmq7qTq.png

After choosing one of the templates, you will be able to adapt it to fit your
application needs in a web text editor.

.. image:: http://i.imgur.com/Z2myJrU.png
    :width: 100%

Click in the **Preview button** to get an idea about how it will look like your
:ref:`task-presenter`.

.. image:: http://i.imgur.com/daRJyLa.png
    :width: 100%

After saving it, you will be able to access your app using the slug, or under
your account in the *Published* applications section:

.. image:: http://i.imgur.com/BXtsCba.png
    :alt: Application Published
    :width: 100%

We recommend to read the 
:doc:`Step by step tutorial on
creating an Application <tutorial>`, as you will understand
how to create the task presenter, which is basically adding some HTML skeleton
to load the task data, input fields to get the answer of the users, and some
JavaScript to make it to work.

.. _api-interface:


Using the API
=============
Creating an application using the API involves also three steps:

    1. Create the application,
    2. Create the :ref:`task-creator`, and 
    3. Create the :ref:`task-presenter` for the users.

Creating the application
~~~~~~~~~~~~~~~~~~~~~~~~

You can create an application via the API URL **/api/app** with a POST request.

You have to provide the following information about the application and convert
it to a JSON object (the actual values are taken from the `Flickr Person demo
application <http://github.com/PyBossa/app-flickrperson>`_)::

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
<http://github.com/PyBossa/app-flickrperson>`_ example, we need to create a JSON object
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

These steps are usually coded in the :ref:`task-creator`. The Flickr Person
Finder applications provides a template for the :ref:`task-creator` that can
be re-used without any problems. Check the createTasks.py_ script for further
details.

.. _createTasks.py: https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py

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
created the tasks, we will need to create the :ref:`task-presenter` for the
application.


Creating the Task Presenter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ref:`task-presenter` is usually a template of HTML and JavaScript that will present the
tasks to the users, and save the answers in the database. The `Flickr Person demo
application <http://github.com/PyBossa/app-flickersperson>`_ provides a simple template
which has a <div> to load the input files, in this case the photo, and another
<div> to load the action buttons that the users will be able to to press to
answer the question and save it in the database. Please, check the :doc:`tutorial` for more details
about the :ref:`task-presenter`.

As we will be using the API for creating the task presenter, we will basically
have to create an HTML file in our computer, read it from a script, and post 
it into PyBossa using the API.

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
creating an Application <tutorial>`, as you will understand
how to create the task presenter, which is basically adding some HTML skeleton
to load the task data, input fields to get the answer of the users, and some
JavaScript to make it to work.
