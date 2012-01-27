===================================
Application Tutorial: Flickr Person
===================================

This tutorial is based in the demo application **Flickr Person** provided with
PyBossa. This demo application is a simple microtasking app where users help
classify photographs by viewing a photograph and then answering a question.

Following the :doc:`general architecture </overview>` of PyBossa the demo
application Flickr Person has two main components:

  * Task Creator: Python script to generate the tasks in PyBossa
  * Task Presenter: HTML + Javascript to show the tasks to the users.

Both applications employ the PyBossa API.

Setting Things Up
=================

You will need to set up an Application object. Details can be found in
:doc:/user/create-application. Creating the tasks themselves will be done by
the Flickr Person task creator script (see next step).


Creating Tasks
==============

We now need to load tasks for your application into PyBossa.

Run the following script::

  python examples/flickrperson.py {optional-path-to-your-pybossa-api}

This script will grab the latest published photos in the Flickr public feed and
save the *link* of the image (the Flickr web page) and the *url* of the image.
For example:

  * Link: http://www.flickr.com/photos/teleyinex/2945647308/
  * URL: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg

Those items will be converted into the following JSON object::

  { 'link': 'http://www.flickr.com/photos/teleyinex/2945647308/',
    'url': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg' }

And saved into the task field **info** of the task model.

.. note::

  Sometimes the script fails because Flickr does not provide a sane JSON feed,
  so you will have to re-run it until you get one successful run.

The script provides an example to use the CRUD methods provided by the API for the application (create_app also reads the application):

.. automodule:: examples.flickrperson
   :members: create_app, update_app, delete_app

Presenting the Tasks to the user
================================

In order to present the tasks to the user, you will only need an HTML template
within PyBossa and a Javascript or any other script language that you want to
use. In this case, Flickr Person uses a basic HTML skeleton and a simple
Javascript library (based on jQuery) to present the tasks to the users (only
anonymous users for the moment) and save the answers.

1. The HTML Skeleton
--------------------

Check the file_ **templates/flickrperson/example.html** for a very basic
skeleton to show the tasks. The file has three sections (div ones):

  * <divs> for the warnings actions. When the user saves an answer, a success
    feedback message is shown to the user. There is also an error one for
    failures.
  * <divs> for the Flickr image. This div will be updated via the Javascript
    with the Flickr Link and image URL for every task.
  * <divs> for the answer buttons. There are three buttons with the possible
    answers: Yes, No, I don't know.

At the end of the skeleton we load the Javascript.

.. _file: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/pybossa/templates/flickrperson/example.html

2. Present the task to the user
-------------------------------

All the action takes place in the file_
**static/flickrPerson/js/flickrperson.js**. The script has several functions to
get from PyBossa the application and its associated tasks. In all
the cases, the calls are using the RESTful API of PyBossa.

First of all we need to get the application ID, so we can check which tasks
are available for the users. The function getApp(name) will get all the
registered applications in PyBossa and get the ID for Flickr Person. In this case, *name*
will have the value "FlickrPerson".

.. js:function:: getApp(name)

   :param string name: The name of the application. 

In this case we use the short name or slug to identify for which application we
want the tasks. If the application is in the system, the function will call the
method **getTask** to obtain all the available tasks for the application.

.. js:function:: getTask(app_id)

   :param integer app_id: Application ID

getTask will obtain all the available tasks in the system (as in the previous
step, for the moment it is not possible to get the task for a given app
ID via the API) and selects those ones that belong to the application. Then, it
choses one randomly and fills in the HTML skeleton with the available
information of the task:

  * the Task ID


3. Saving the answer
--------------------

Once the task has been presented, the users can click the answer buttons: **Yes**, **No** or **I don't know**.
Yes and No save the answer in the DB (check **/api/taskrun**) with information about the task and the answer,
while the button **I don't know** simply loads another task as sometimes the
image is not available (the Flickr user has delete it) or it is not clear if
there is a human or not in the image (you only see one hand and nothing else). 

flickrperson.js uses the function submitTask(answer) to stores the answer:

.. js:function:: submitTask(answer)

   :parameter string answer: 'Yes' or 'No' values

The function gets the answer from the button and embeds it in the *info* field of a JSON object::

  'info': {'answer': answer}

Please, read the `example file
<https://github.com/citizen-cyberscience-centre/pybossa/blob/master/pybossa/templates/flickrperson/example.html>`_
for more details about all the steps.


4. Test the task presenter
--------------------------

In order to test the task presenter, you only have to load the main page of
PyBossa:

 * http://0.0.0.0:5000

And click in the big blue button: Start contributing now.

