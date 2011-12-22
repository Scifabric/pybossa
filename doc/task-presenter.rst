=======================
Task Presenter Tutorial
=======================

This tutorial is based in the demo application **Flickr Person** provided with PyBossa.

Flickr Person
=============

The demo application Flickr Person has two main components:

  * Python script to generate the tasks in PyBossa, and
  * HTML + Javascript to show the tasks to the users.

Both applications employ the PyBossa API.

1. Create the application
=======================================

First of all we have to create an application for the project. The application will be created using the API URL **/api/app** with a POST action. We will have to provide the following information about the application and convert it to a JSON object::

  name = u'Flickr Person Finder'
  short_name = u'FlickrPerson'
  description = u'Do you see a human in this photo?'
  data = dict(name = name, short_name = short_name, description = description)
  data = json.dumps(data)

The **description** field is used to store the **question** that we want to ask in our tasks. As Flickr Person is trying to figure out if there is a person in the photo, the question is: *Do you see a human in this photo?*. The other two fields are the names used for naming the application (short_name will be the slug name of the application).

Please, check the following script lines_ for more information.

.. _lines: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L25

2. Create a batch for the application
=====================================

Once the application has been created, a batch of tasks can be created associated to the application **ID**. The following fields have to be provided::

  name = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")                                                                                                   
  data = dict (name = name, app_id = app_id, calibration = 0)
  data = json.dumps(data)

We use the creation time of the batch as name, but it possible to use whatever you like. 

As you can see, all the data is sent in JSON format. The API URL to POST the data is: **/api/batch**.

Please, check the following script lines_ for more information.
.. _lines: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L63

3. Create the tasks
===================

The last step involves the creation of tasks associated to a **batch** and an **application**. As in all the previous steps, we are going to create a JSON object and POST it using the following API URL **/api/task**::

  info = dict (link = photo['link'], url = photo['url'])
  data = dict (app_id = app_id, batch_id = batch_id, state = 0, info = info, calibration = 0, priority_0 = 0)
  data = json.dumps(data)

The most important field for the task is the **info** one. This field will be used to store a JSON object with the required data for the task. As Flickr Person is trying to figure out if there is a human or not in a photo, the provided information is: the Flickr Link page of the photo, and the image URL of the photo. If your application needs more fields, you are free to add them based on your needs.

Please, check the following script lines_ for more information.
.. _lines: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L83

Testing Flickr Person Demo Application
======================================

We have seen all the required steps to create an application with a batch of tasks. If you want to test it, make sure that you have a running version of PyBossa in your machine, and run the following script  **flickrPerson/getPhotos.py**. This script will grab the latest published photos in the Flickr public feed and save the *link* of the image (the Flickr web page) and the *url* of the image. For example:

  * Link: http://www.flickr.com/photos/teleyinex/2945647308/
  * URL: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg

Those items will be converted into the following JSON object::

  { 'link': 'http://www.flickr.com/photos/teleyinex/2945647308/', 'url': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg' }

And saved into the task field **info** of the task model. **Note**: sometimes the script fails because Flickr does not provide a sane JSON feed, so you will have to re-run it until you get one successful run.

Presenting the Tasks to the user
================================

In order to present the tasks to the user, you will only need an HTML template within PyBossa and a Javascript or any other script language that you want to use. In this case, Flickr Person uses a basic HTML skeleton and a simple Javascript library (based on jQuery) to present the tasks to the users (only anonymous users for the moment) and save the answers.

1. The HTML Skeleton
====================

Check the file_ **templates/flickrperson/example.html** for a very basic skeleton to show the tasks. The file has three sections (div ones):
  * <divs> for the warnings actions. When the user saves an answer, a success feedback message is shown to the user. There is also an error one for failures.
  * <divs> for the Flickr image. This div will be updated via the Javascript with the Flickr Link and image URL for every task.
  * <divs> for the answer buttons. There are three buttons with the possible answers: Yes, No, I don't know.

At the end of the skeleton we load the Javascript.

.. _file: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/pybossa/templates/flickrperson/example.html

2. Present the task to the user
===============================

All the action takes place in the file_ **static/flickrPerson/js/flickrperson.js**. The script has several functions to get from PyBossa the application and its associated batches and tasks. In all the cases, the calls are using the RESTful API of PyBossa.

First of all we need to get the application ID, so we can check which batches are available for the users. The function getApp(name) will get all the registered applications in PyBossa and get the ID for Flickr Person::

  getApp("FlickrPerson")

In this case we use the short name or slug to identify for which application we want the tasks. If the application is in the system, the function will call the method **getBatches** to obtain all the available batches for the application.

getBatches obtains all the available batches in the system (for the moment it is not possible get all the batches for a given application via the API), and then checks which ones belong to FlickrPerson. The method uses the simplest approach and choses randomly one of the available batches, and calls the next function to get all the tasks associated to that batch: **getTask**.

getTask will obtain all the available tasks in the system (as in the previous step, for the moment is not possible to get the task for a given batch or app ID via the API) and selects those ones that belong to the batch. Then, it choses one randomly and fills in the HTML skeleton with the available information of the task:

  * the Batch ID, and 
  * the Task ID.

The users then can click Yes, No or I don't know. Yes and No save the answer in the DB (check **/api/taskrun**) with information about the task and the answer, while the button **I don't know** simply loads another task as sometimes the image is not available (the Flickr user has delete it) or it is not clear if there is a human or not in the image (you only see one hand and nothing else). 

Please, read the file_ for more details about all the steps.

.. _file: https://github.com/citizen-cyberscience-centre/pybossa/blob/master/pybossa/templates/flickrperson/example.html

3. Test the task presenter
==========================

In order to test the task presenter, you only have to load the main page of PyBossa:

 * http://0.0.0.0:5000

And click in the big blue button: Start contributing now.
