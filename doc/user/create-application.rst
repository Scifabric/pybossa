====================================
Creating a Crowdsourcing Application
====================================

Readers may wish to start with the :doc:`Step by step tutorial on creating an
Application <create-application-tutorial>` which walks through creating a
simple photo classification App.

1. Create the Application itself
================================

First of all we have to create an application for the project.

Via the Web Interface
---------------------

The standard way to do this is in the web interface. However, this is not yet operational!

Via the API
-----------

You can create an application via the API URL **/api/app** with a POST request.

You have to provide the following information about the application and convert
it to a JSON object (the actual values are taken fromthe Flickr Person demo
project)::

  name = u'Flickr Person Finder'
  short_name = u'FlickrPerson'
  description = u'Do you see a human in this photo?'
  data = dict(name = name, short_name = short_name, description = description)
  data = json.dumps(data)

The **description** field is used to store the **question** that we want to ask
in our tasks. As Flickr Person is trying to figure out if there is a person in
the photo, the question is: *Do you see a human in this photo?*. The other two
fields are the names used for naming the application (short_name will be the
slug name of the application).

Please, check the following script `lines
<https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L25>`_
for more information.


2. Create a batch for the application
=====================================

**Deprecated**

Once the application has been created, a batch of tasks can be created
associated to the application **ID**. The following fields have to be
provided::

  name = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")                                                                                                   
  data = dict (name = name, app_id = app_id, calibration = 0)
  data = json.dumps(data)

We use the creation time of the batch as name, but it possible to use whatever
you like. 

As you can see, all the data is sent in JSON format. The API URL to POST the
data is: **/api/batch**.

Please, check the following script `lines
<https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L63>`_
for more information.

3. Create the Tasks
===================

The last step involves the creation of tasks associated to a **batch** and an
**application**. As in all the previous steps, we are going to create a JSON
object and POST it using the following API URL **/api/task**::

  info = dict (link = photo['link'], url = photo['url'])
  data = dict (app_id = app_id, batch_id = batch_id, state = 0, info = info, calibration = 0, priority_0 = 0)
  data = json.dumps(data)

The most important field for the task is the **info** one. This field will be
used to store a JSON object with the required data for the task. As Flickr
Person is trying to figure out if there is a human or not in a photo, the
provided information is: the Flickr Link page of the photo, and the image URL
of the photo. If your application needs more fields, you are free to add them
based on your needs.

Please, check the following script `lines
<https://github.com/citizen-cyberscience-centre/pybossa/blob/master/flickrPerson/getPhotos.py#L83>`_
for more information.

4. Specify a Task Presenter
===========================

You now need to provide a task presenter for your application. See the detailed
example of creating a Task Presenter in the :doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`.

