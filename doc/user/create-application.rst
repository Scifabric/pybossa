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
  data = dict(name = name, short_name = short_name, description = description, hidden = 0)
  data = json.dumps(data)

The **description** field is used to store the **question** that we want to ask
in our tasks. As Flickr Person is trying to figure out if there is a person in
the photo, the question is: *Do you see a human in this photo?*. The other two
fields are the names used for naming the application (short_name will be the
slug name of the application). Finally, the *hidden* field is a bool flag to hide the 
application for users but not administrators (roles will be implemented soon).

.. automodule:: examples.flickrperson
   :members: create_app, get_flickr_photos

3. Create the Tasks
===================

The last step involves the creation of tasks associated to an
**application**. As in all the previous steps, we are going to create a JSON
object and POST it using the following API URL **/api/task**::

  info = dict (link = photo['link'], url = photo['url'])
  data = dict (app_id = app_id, state = 0, info = info, calibration = 0, priority_0 = 0)
  data = json.dumps(data)

The most important field for the task is the **info** one. This field will be
used to store a JSON object with the required data for the task. As Flickr
Person is trying to figure out if there is a human or not in a photo, the
provided information is: the Flickr Link page of the photo, and the image URL
of the photo. If your application needs more fields, you are free to add them
based on your needs.

.. automodule:: examples.flickrperson
   :members: create_task

4. Specify a Task Presenter
===========================

You now need to provide a task presenter for your application. See the detailed
example of creating a Task Presenter in the :doc:`Step by step tutorial on
creating an Application <create-application-tutorial>`.

