===================================
Application Tutorial: Flickr Person
===================================

This tutorial is based in the demo application **Flickr Person** (`source code`_) provided with
PyBossa. This demo application is a simple microtasking application where users have to
answer the following question: *Do you see a human in this photo?* The possible
answers are: *Yes, No* and *I don't know*.

.. _source code: https://github.com/PyBossa/app-flickrperson

The demo application Flickr Person has two main components:

  * The **Task Creator**: a Python script that creates the tasks in PyBossa, and
  * the **Task Presenter**: an HTML + Javascript structure that will show the tasks 
    to the users and save their answers.

Both items use the PyBossa API.

Setting Things Up
=================

In order to run the tutorial, you will need to create an account in a PyBossa
server. The PyBossa server could be running in your computer or in a third party
server.

.. note::

   You can use http://pybossa.com for testing. 

When you create the account, you will have to access your profile, and copy the
**API-KEY** that has been generated for you. This **API-KEY** allows you to create the
application in PyBossa (only authenticated users can create applications and
tasks, while everyone can collaborate solving the tasks).

Creating the Application
========================

There two possible ways for creating an application:

  * Using the **web interface**: click in your user name, and you will
    see a section named **applications** list. In that section you will be able
    to create an application using the web interface.
  * Using the **RestFUL API**: you can check the source code of the
    createTasks.py script for more details about creating an application using
    the API.

For this tutorial we are going to use the second option, the *RestFUL API* via
the *createTasks.py* script. This script has two mandatory arguments:

    * the URL of the PyBossa server, and 
    * an API-KEY to authenticate you in the PyBossa server. 

The following section gives more details about how to use the script.

.. note::
    If you are running a PyBossa server locally, you can omit the URL parameter
    as by default it uses the URL http://localhost:5000

Creating the Tasks and Application
==================================

The createTasks.py_ script has a full example about how to create
an application and several tasks for the application. PyBossa will deliver the
tasks for the users (authenticated and anonymous ones) and store the submitted
answers in the PyBossa data base.

.. _createTasks.py: https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py

The script gets the latest 20 published photos from the public Flickr feed and
saves the *link* of the Flickr web page publishing the photo, as well as the 
*direct url* of the image.

For example:

  * **Link**: http://www.flickr.com/photos/teleyinex/2945647308/
  * **URL_m**: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg
  * **URL_b**: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_b.jpg

.. note::

    Flickr creates from the original image, different cropped versions of the
    image. Flickr uses a pattern to distinguish them: **_m** for medium size,
    and **_b** for the big ones. There are more options, so if you need more
    help in this matter, check the official Flickr documentation.

Those three variables (Link URL_m and URL_b) will be stored in a JSON object::

  { 'link': 'http://www.flickr.com/photos/teleyinex/2945647308/',
    'url_m': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg', 
    'url_b': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_b.jpg' }

And saved into the task field **info** of the task model. As Flickr only
publishes the latest 20 uploaded photos in their public feed, the script will
create only 20 tasks in PyBossa.

In order to create the application and its tasks, run the following script::

  python createTasks.py -u http://PYBOSSA-SERVER -k API-KEY -c

Providing more details about the application
============================================

If you check the source code, you will see that there is a file named
*long_description.html*. This file has a long description of the application,
explaining different aspects of it.

This information is not mandatory, however it will be very useful for the users
as they will get a bit more of information about the application goals.

The file can be composed using HTML or plain text. As PyBossa is using `Twitter
Bootstrap <http://twitter.github.com/bootstrap/>`_ you can use all the available 
CSS properties that this framework provides.

The long description is shown in the application home page::

 http://pybossa.com/app/flickrperson

If you want to modify the description you have two options:

 * Edit it via the web interface, or
 * modify locally the *long_description.html* file and run the command again
   with the **-t** option to update it.


Adding an icon to the application
=================================

It is possible also to add a nice icon for the application. By default PyBossa
will render a 100x100 pixels empty thumbnail for those applications that do not
provide it. If you want to add an icon you only have to upload the thumbnail of
size 100x100 pixels to a hosting service like Flickr, ImageShack, etc. and use
the URL image link to include it in the **info** field (check createTask.py
script as it has an example)::

  info = { 'thumbnail': http://hosting-service/thumbnail-name.png,
           'task_presenter': template.html file,
           'tutorial': tutorial.html
         }

Presenting the Tasks to the user
================================

In order to present the tasks to the user, you have to create an HTML template.
The template is the skeleton that will be used to load the tasks data (the photos
images) and the questions and answers that users can provide for the given
task.

In this tutorial, Flickr Person uses a basic HTML skeleton and the `PyBossa.JS
<http://pybossajs.rtfd.org>`_ library to load the data of the tasks into the 
HTML template, and take actions based on the users's answers.

.. note::
  When a task is submitted by an authenticated user, the task will save his
  user_id. For anonymous users the submitted task will only have the user IP
  address.

Creating a tutorial for the users
=================================

In general, users will like to have some feedback when accessing for the very
first time your application. Usually, the overview page of your application
will not be enought, so you can actually build a tutorial (a web page) that
will explain to the volunteer how he can participate in the application.

PyBossa will detect if the user is accessing for the very first time your
application, so in that case, it will load the **tutorial** if your application
has one.

Adding a tutorial is really simple: you only have to create a file named
**tutorial.html** and add it to the **info** object::

  info = { 'thumbnail': http://hosting-service/thumbnail-name.png,
           'task_presenter': template.html file,
           'tutorial': tutorial.html
         }

The tutorial could have whatever you like: videos, nice animations, etc.
PyBossa will render for you the header and the footer, so you only have to
focus on the content. You can actually copy the template.html file and use it
as a draft of your tutorial or just include a video of yourself explaining why 
your project is important and how, as a volunteer, you can contribute.

If your application has a tutorial, you can actually access it directly in this
endpoint::

  http://server/app/tutorial


1. The HTML Skeleton
--------------------

The file_ **template.html** has the skeleton to show the tasks. The file has three 
sections or <div>:

  * **<div> for the warnings actions**. When the user saves an answer, a success
    feedback message is shown to the user. There is also an error one for
    the failures.
  * **<div> for the Flickr image**. This div will be populated with the task
    photo URL and LINK data.
  * **<div> for the Questions & Answer buttons**. There are three buttons with the 
    possible answers: *Yes*, *No*, and *I don't know*.

At the end of the skeleton we load the Javascript: 

 * the PyBossa.JS library: <script src="/static/js/pybossa/pybossa.js" type="text/javascript"></script>
 * and the script to load the data, request new tasks, etc.: <script></script>

.. _file: https://github.com/PyBossa/app-flickrperson/blob/master/app-flickrperson/template.html

This template file will be used by the **createTasks.py** script to send the
template as part of the JSON object that will create the application. In PyBossa
every application has a **presenter** endpoint:

 * http://PYBOSSA-SERVER/app/SLUG/presenter

.. note::
   The **slug** is the short name for the application, in this case **flickrperson**. 

Loading the above endpoint will load the skeleton and trigger the JavaScript 
functions to get a task from the PyBossa server and populate it in the HTML
skeleton.

The header and footer for the presenter are already provided by PyBossa, so the 
template only has to define the structure to present the data from the tasks to the
users and the action buttons, input methods, etc. to retrieve and save the 
answer from the volunteers.

2. Updating the template for all the tasks
------------------------------------------

It is possible to update the template of the application without
having to re-create the application and its tasks. In order to update the
template, you only have to modify the file template.html and run the following
command::

  python createTasks.py -u http://PYBOSSA-SERVER -k API-KEY -t

3. Loading the Task data
------------------------

All the action takes place in the file_
**template.html** script section, after the pybossa.js library.

The script is very simple, it uses the  `PyBossa.JS library
<http://pybossajs.rtfd.org>`_ to get a new task and
to submit and save the answer in the server.

`PyBossa.JS <http://pybossajs.rtfd.org>`_ provides a method to get the data 
for a task that needs to be solved by the volunteer:

  * pybossa.newTask( applicationName )

In this case, *applicationName* will be "flickrperson". The library will get
a task for the application and return a JSON object with the following
structure::

  { question: application.description,
    task: { 
            id: value,
            ...,
            info: { 
                    url_m: 
                    link:
                   } 
          } 
  }

Therefore, if we want to load the data into the skeleton, we will only have to
do something like this::

  $("#question h1").text(data.question);
  $("#task-id").text(data.task.id);
  $("#photo-link").attr("href", data.task.info.link);
  $("#photo").attr("src",data.task.info.url_m);

and wrap it in the *pybossa.newTask* method::

  pybossa.newTask( "flickrperson").done(
    function( data ) {
      $("#question h1").text(data.question);
      $("#task-id").text(data.task.id);
      $("#photo-link").attr("href", data.task.info.link);
      $("#photo").attr("src",data.task.info.url_m);
    };
  );

Every time that we want to load a new task, we will have to call the above
function, so it will be better if we create a specific function for this
purpose (check the *loadData* function in the script).

At some point the user will not receive more tasks for the application, so it
will be really helpful for the user to flash a message giving thanks to the
user. In the warnings section, we have a specific div to show the finish
message to the user, saying thank you to the user and inviting him to help in
other applications. As the skeleton is no longer useful, there is no more
images that will be loaded for this user, it should be hidden.Thus, in the
**loadData** function we could run the following test to see if we have to load
the image, or pop-up the finish message::

  if ( !$.isEmptyObject(data.task) ) {
     spinnerStart();
     $("#question h2").text(data.question);
     $("#task-id").text(data.task.id);
     $("#photo-link").attr("href", data.task.info.link);
     $("#photo").attr("src",data.task.info.url_m);
  }
  else {
     $(".skeleton").hide();
     $("#finish").fadeIn();
  }

Once the data have been loaded, it is time to bind the buttons *onclick*
events to functions that will save the answer from the user in the data base.

4. Saving the answer
--------------------

Once the task has been presented, the users can click on the answer buttons:
**Yes**, **No** or **I don't know**.

*Yes* and *No* save the answer in the DB (check **/api/taskrun**) with information 
about the task and the answer, while the button *I don't know* simply loads another 
task as sometimes the image is not available (the Flickr user has delete it) or it 
is not clear if there is a human or not in the image (you only see one hand and 
nothing else).

In order to submit and save the answer from the user, we will use again the `PyBossa.JS 
library <http://pybossajs.rtfd.org>`_. In this case::

  pybossa.saveTask( taskid, answer )

The *pybossa.saveTask* method saves an answer for a given task. In the
previous section we saved in the DOM the *task-id* that we have loaded, so we can
retrieve this value and use it for saving the volunteer's answer (it can be
also saved in a variable if you want).

The method allows us to give a successful pop-up feedback for the user, so we
will use the following structure to warn the user and tell him that his answer
has been saved and then load a new Task::

  pybossa.saveTask( taskid, answer ).done(
    function( data ) {
        // Show the feedback div
        $("#success").fadeIn(); 
        // Fade out the pop-up after a 1000 miliseconds
        setTimeout(function() { $("#success").fadeOut() }, 1000);
        // Finally, load a new task
        pybossa.newTask("flickrperson").done( function( data ){ loadData( data ) });
    };
  );

Now we only have to bind the action of the *Yes*, *No* and *I don't know* buttons to call the above
snippet. In order to bind it, we will use the *onclick event* to call a new and
simple function for both buttons::

  <button class="btn btn-success" onclick="submitTask('Yes')">Yes</button>
  <button class="btn btn-info" onclick="submitTask('No')">No</button>
  <button class="btn" onclick="submitTask('DontKnow')">I don't know</button>

The function *submitTask* will get the *task-id* from the DOM, and the answer is
the string 'Yes' or 'No' depending on which button the user has clicked. The
only missing button is the "I don't know" which will use the same event,
*onclick*, to request a new task using the *pybossa.newTask* function::

 <button class="btn" onclick="pybossa.newTask('flickrperson').done( function( data ) { loadData( data ) });">I don't know</button>

For more details about the code, please, check the `template file
<https://github.com/PyBossa/app-flickrperson/blob/master/app-flickrperson/template.html>`_.

4. Test the task presenter
--------------------------

In order to test the application task presenter, go to the following URL::

  http://PYBOSSA-SERVER/app/SLUG/presenter

The presenter will load one task, and you will be able to submit and save one
answer for the current task.

5. Check the results
--------------------

In order to see the answers from the volunteers, you can open in your web
browser the file **results.html**. The web page should show a chart pie with
answers from the server http://pybossa.com but you can modify the file
**results.js** to poll your own server data.
¬                                                                                    
The results page shows the number of answers from the volunteers for a given
task (the related photo will be shown), making easy to compare the results
submitted by the volunteers.

The results page is created using the `D3.JS library <http://d3js.org>`_.
