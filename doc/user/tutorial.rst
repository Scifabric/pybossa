====================
Application Tutorial
====================

This tutorial is based in the demo application **Flickr Person** (`source code`_) provided with
PyBossa. This demo application is a simple microtasking application where users have to
answer the following question: *Do you see a human in this photo?* The possible
answers are: *Yes, No* and *I don't know*.

.. _source code: https://github.com/PyBossa/app-flickrperson

The demo application Flickr Person has two main components:

  * The :ref:`task-creator` a Python script that creates the tasks in PyBossa, and
  * the :ref:`task-presenter`: an HTML + Javascript structure that will show the tasks 
    to the users and save their answers.

Both items use the PyBossa API.

Setting Things Up
=================

In order to run the tutorial, you will need to create an account in a PyBossa
server. The PyBossa server could be running in your computer or in a third party
server.

.. note::

   You can use http://crowdcrafting.org for testing. 

When you create an account, you will have access to your profile by clicking on your 
name, and then in the **My Settings** option:

.. image:: http://i.imgur.com/nH9u2nk.png

Then, you will be able to copy the
`API-KEY that has been generated for you <http://crowdcrafting.org/account/profile>`_ 

.. image:: http://i.imgur.com/aTooi6Q.png

This **API-KEY** allows you to create the
application in PyBossa (only authenticated users can create applications and
tasks, while everyone can collaborate solving the tasks).

.. note::

    The Flickr Person Finder demo application uses the third party libraries
    that need to be installed in your system before proceeding. For this
    reason, we recommend you to configure a `virtualenv`_  for the application 
    as it will create a an isolated Python environment in a folder, 
    helping you to manage different dependencies and
    versions without having to deal with root permissions in your server machine.

    virtualenv_ creates an environment that has its own installation directories, 
    that doesn't share libraries with other virtualenv environments (and 
    optionally doesn't access the globally installed libraries either).
    
    You can install the software if you want at the system level if you have root
    privileges, however this may lead to broken dependencies in the OS for all your
    Python packages, so if possible, avoid this solution and use the virtualenv_
    solution.

.. _virtualenv: http://pypi.python.org/pypi/virtualenv


.. note:: 

    Flickr Person Finder uses the **pybossa-client** module which simplifies a lot
    accessing the PyBossa services and API endpoints. Therefore, you will need to
    install the *pybossa-client* with `pip --a python installer packager <http://pypi.python.org/pypi/pip>`_::

    $ pip install pybossa-client

.. note::
    
    If you need to install **pip** in your system, check `the official
    documentation. <http://www.pip-installer.org/en/latest/installing.html>`_

Creating the Application
========================

There two possible ways for creating an application:

  * :ref:`web-interface`: click in your user name, and you will
    see a section named **applications** list. In that section you will be able
    to create an application using the web interface.
  * :ref:`api-interface`: you can check the source code of the
    `createTasks.py script <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_ 
    for more details about creating an application using the API.

For this tutorial we are going to use the second option, the :doc:`../api` via
the `createTasks.py script <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_. 
This script has two mandatory arguments:

    * the URL of the PyBossa server, and 
    * an API-KEY to authenticate you in the PyBossa server. 

The following section gives more details about how to use the script.

.. note::
    If you are running a PyBossa server locally, you can omit the URL parameter
    as by default it uses the URL http://localhost:5000

Cloning the Flickr Person Finder source code
--------------------------------------------

In order to follow the tutorial, you will need to clone the `Flickr Person
Finder public Github Repository <http://github.com/PyBossa/app-flickrperson>`_
so you will have a local copy of the required files to create the application
and tasks using the API.

.. image:: http://i.imgur.com/CYPnPft.png

If you are new to Github and the GIT software, we recommend you to take this
`free and on-line course <http://try.github.com>`_ (it will take you only
15 minutes!) where you will learn the basics, which are the main concepts that
you will need for cloning the demo app repository.

If you prefer to skip the course and take it in a later stage, the commands
that you need to clone the repository are::

    git clone git://github.com/PyBossa/app-flickrperson.git

After running that command a new folder named **app-flickrperson** will be
created from where you run the command. If you don't like the command line, you
can try the free `MAC <http://mac.github.com/>`_ or 
`Windows <http://windows.github.com/>`_ Github applications. If you use a GNU/Linux
OS there are several GUI for git, `search in your distribution packages system
<http://packages.ubuntu.com/search?suite=quantal&section=all&arch=any&keywords=git+gui&searchon=all>`_.


Configuring the name, short name, thumbnail, etc.
=================================================

The Flickr Person Finder provides a file called: `app.json <https://github.com/PyBossa/app-flickrperson/blob/master/app.json>`_  that has the
following content::

    {
        "name": "Flickr Person Finder",
        "short_name": "flickrperson",
        "thumbnail": "http://imageshack.us/a/img37/156/flickrpersonthumbnail.png",
        "description": "Image pattern recognition",
        "question": "Do you see a human in this photo?"
    }

You will need to modify the **name** and **short_name** fiels in order to
create an application in crowdcrafting.org, as there is already an application
registered with those values.

.. note::

    The **name** and **short_name** of the application **must be unique**!
    Otherwise you will get an error (IntegrityError) when creating the application.

You can re-use the other fields if you want. **Description** will be the text
shown in the application listing page, and the **question** field is the
question that will be shown to the users when they collaborate with your
project.

Creating the Tasks and Application
==================================

The `createTasks.py script <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_
has a full example about how to create
an application and several tasks for the application. PyBossa will deliver the
tasks for the users (authenticated and anonymous ones) and store the submittedd
answers in the PyBossa data base.

The script gets the latest 20 published photos from the public Flickr feed and
saves the *link* of the Flickr web page publishing the photo, as well as the 
*direct url* of the image.

For example:

  * **Link**: http://www.flickr.com/photos/teleyinex/2945647308/
  * **URL_m**: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg
  * **URL_b**: http://farm4.staticflickr.com/3208/2945647308_f048cc1633_b.jpg

.. note::

    Flickr creates from the original image different cropped versions of the
    image. It uses a pattern to distinguish them: **_m** for medium size,
    and **_b** for the big ones. There are more options, so if you need more
    help in this matter, check the official `Flickr documentation <http://www.flickr.com/services/api/>`_.

Those three variables (Link URL_m and URL_b) will be stored in a JSON object::

  { 'link': 'http://www.flickr.com/photos/teleyinex/2945647308/',
    'url_m': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg', 
    'url_b': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_b.jpg' }

And saved into the task field **info** of the task model. As Flickr only
publishes the latest 20 uploaded photos in their public feed, the script will
create only 20 tasks in PyBossa.

Finally the script will read the `app.json <https://github.com/PyBossa/app-flickrperson/blob/master/app.json>`_ file to create the application
and associated tasks. In order to create the application and its tasks, 
run the following script::

  python createTasks.py -s http://PYBOSSA-SERVER -k API-KEY -c


.. note::
    You can check all the available options for the command line with the
    **-h** argument.

If something goes wrong, you should an error message similar to the following
one::

    ERROR:root:pbclient.create_app
    {
        "action": "POST",
        "exception_cls": "IntegrityError",
        "exception_msg": "(IntegrityError) duplicate key value violates unique constraint \"app_name_key\"\nDETAIL:  Key (name)=(Flickr Person Finder) already exists.\n",
        "status": "failed",
        "status_code": 415,
        "target": "app"
    }

The error message will have the information regarding the problems it has found
when using the API.

Number of answers or task runs per task
=======================================

PyBossa by default will send a task to different users (authenticated and
anonymous users) until 30 different task runs are obtained for each task. 

:ref:`task-scheduler` does not allow the same user to submit more than one answer for 
any task (even 'anonymous' users who are not logged in, are recognised via 
their IP address).

This value, 30 answers, can be changed for each task without problems in the 
:ref:`task-redundancy` section or using the API. If you want
to improve the quality of the results for one task and get more confidence on
the data when you will analyze it, you can specify it in the task JSON object
if you use the API::

    { 
        'app_id': your application id,
        'info': the previous JSON object,
        'n_answers': 100
    }

In this case the **n_answers** field will make :ref:`task-scheduler` to try and 
obtain 100 different answers from different users for each task.

The `createTasks.py script <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_ has a command line argument that allows you to
change the number of task runs that you want per task. Check the source code
for more information.

Changing the Priority of the tasks
==================================

Every task can have its own **priority**. The :ref:`task-priority` can be configured using
the web interface, or the API.

A task with a higher priority will be delivered first to the volunteers. Hence if you 
have a project where you need to analyze a task first due
to an external event (a new data sample has been obtained), then you can modify 
the priority of the new created task and deliver it first. 

Using the API for changing the priority will be as simple as specifying in the task 
JSON object the following::

    { 
        'app_id': your application id,
        'info': the previous JSON object,
        'priority_0': 0.9
    }

The priority is a number between 0.0 and 1.0. The highest priority is 1.0 and
the lowest is 0.0. 

Providing more details about the application
============================================

If you check the source code, you will see that there is a file named
*long_description.html*. This file has a long description of the application,
explaining different aspects of it.

This information is not mandatory, however it will be very useful for the users
as they will get a bit more of information about the application goals.

The file can be composed using HTML or plain text. As PyBossa is using `Twitter
Bootstrap <http://twitter.github.com/bootstrap/>`_ you can use all the available 
CSS styles that this framework provides, as well as the icons provided by the
project `Font Awesome <http://fortawesome.github.com/Font-Awesome/>`_

The long description will be shown in the application home page::

 http://crowdcrafting.org/app/flickrperson

If you want to modify the description you have two options:

 * Edit it via the web interface, or
 * modify locally the *long_description.html* file and run the command again
   with the **-t** option to update it.


Adding an icon to the application
=================================

It is possible also to add a nice icon for the application. By default PyBossa
will render a 100x100 pixels empty thumbnail for those applications that do not
provide it. 

If you want to add an icon you only have to upload the thumbnail of
size 100x100 pixels to a hosting service like Flickr, Imgur, ImageShack, etc. 

In order to include a thumbnail all you have to do is to modify the
`app.json <https://github.com/PyBossa/app-flickrperson/blob/master/app.json>`_
file and paste the direct link to the icon in the **thumbnail**
field::

    {
        "name": "Flickr Person Finder",
        "short_name": "flickrperson",
        "thumbnail": "http://imageshack.us/a/img37/156/flickrpersonthumbnail.png",
        "description": "Image pattern recognition",
        "question": "Do you see a human in this photo?"
    }


Presenting the Tasks to the user
================================

In order to present the tasks to the user, you have to create an HTML template.
The template is the skeleton that will be used to load the data of the tasks:
the question, the photos, user progress, and input fields & submit buttons 
to solve the task. 

In this tutorial, Flickr Person uses a basic HTML skeleton and the `PyBossa.JS
<http://pybossajs.rtfd.org>`_ library to load the data of the tasks into the 
HTML template, and take actions based on the users's answers.

.. note::
  When a task is submitted by an authenticated user, the task will save his
  user_id. For anonymous users the submitted task will only have the user IP
  address.


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

By default, the PyBossa framework loads for every task the PyBossa.JS library,
so you don't have to include it in your template.

All you have to do is to add a script section where you will be loading the
tasks and saving the answers from the users: <script></script>.

.. _file: https://github.com/PyBossa/app-flickrperson/blob/master/app-flickrperson/template.html

This template file will be used by the `createTasks.py <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_ script to send the
template as part of the JSON object that will create the application. 

.. note::
    You can also edit the HTML skeleton using the web interface. Once the
    application has been created in PyBossa you will see a button that allows
    you to edit the skeleton using a WYSIWYG editor.

In PyBossa every application has a **presenter** endpoint:

 * http://PYBOSSA-SERVER/app/SLUG/newtask

.. note::
   The **slug** is the short name for the application, in this case 
   **flickrperson**. 

Loading the above endpoint will load the skeleton and trigger the JavaScript 
functions to get a task from the PyBossa server and populate it in the HTML
skeleton.

The header and footer for the presenter are already provided by PyBossa, so the 
template only has to define the structure to present the data from the tasks to the
users and the action buttons, input methods, etc. to retrieve and save the 
answer from the volunteers.

1.1. Flickr Person Skeleton
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Flickr Person Finder demo we have a very simple DOM. At the beginning
you will find a big div that will be used to show some messages to the user
about the success of an action, for instance that an answer has been saved or
that a new task is being loaded:

.. code-block:: html

    <div class="row">
      <!-- Success and Error Messages for the user --> 
      <div class="span6 offset2" style="height:50px">
        <div id="success" class="alert alert-success" style="display:none;">
          <a class="close">×</a>
          <strong>Well done!</strong> Your answer has been saved
        </div>
        <div id="loading" class="alert alert-info" style="display:none;">
          <a class="close">×</a>
          Loading next task...
        </div>
        <div id="taskcompleted" class="alert alert-info" style="display:none;">
          <strong>The task has been completed!</strong> Thanks a lot!
        </div>
        <div id="finish" class="alert alert-success" style="display:none;">
          <strong>Congratulations!</strong> You have participated in all available tasks!
          <br/>
          <div class="alert-actions">
            <a class="btn small" href="/">Go back</a>
            <a class="btn small" href="/app">or, Check other applications</a>
          </div>
        </div>
        <div id="error" class="alert alert-error" style="display:none;">
          <a class="close">×</a>
          <strong>Error!</strong> Something went wrong, please contact the site administrators
        </div>
      </div> <!-- End Success and Error Messages for the user -->
    </div> <!-- End of Row -->

Then we have the skeleton where we will be loading the Flickr photos, and
the submission buttons for the user.

First it creates a row that will have two columns (in Bootstrap a row can have
12 columns), so we will populate a structure like this:

.. code-block:: html

    <div class="row skeleton">
        <!-- First column for showing the question, submission buttons and user
        progress -->
        <div class="span6"></div>
        <!-- Second column for showing the Flickr photo -->
        <div class="span6"></div>
    </div>


The content for the first column where we will be showing the question of the
task, the submission buttons with the answers: yes, no, and I don't know, and
obviously the user progress for the user, so he can know how many tasks he has
completed and how many are left. The code is the following:

.. code-block::html

    <div class="span6 "><!-- Start of Question and Submission DIV (column) -->
        <h1 id="question">Question</h1> <!-- The question will be loaded here -->
        <div id="answer"> <!-- Start DIV for the submission buttons -->
            <!-- If the user clicks this button, the saved answer will be value="yes"-->
            <button class="btn btn-success btn-answer" value='Yes'><i class="icon icon-white icon-thumbs-up"></i> Yes</button>
            <!-- If the user clicks this button, the saved answer will be value="no"-->
            <button class="btn btn-danger btn-answer" value='No'><i class="icon icon-white icon-thumbs-down"></i> No</button>
            <!-- If the user clicks this button, the saved answer will be value="NotKnown"-->
            <button class="btn btn-answer" value='NotKnown'><i class="icon icon-white icon-question-sign"></i> I don't know</button>
        </div><!-- End of DIV for the submission buttons -->
        <!-- Feedback items for the user -->
        <p>You are working now on task: <span id="task-id" class="label label-warning">#</span></p>
        <p>You have completed: <span id="done" class="label label-info"></span> tasks from
        <!-- Progress bar for the user -->
        <span id="total" class="label label-inverse"></span></p>
        <div class="progress progress-striped">
            <div id="progress" rel="tooltip" title="#" class="bar" style="width: 0%;"></div>
        </div>
        <!-- 
            This application uses Disqus to allow users to provide some feedback.
            The next section includes a button that when a user clicks on it will
            load the comments, if any, for the given task
        -->
        <div id="disqus_show_btn" style="margin-top:5px;">
            <button class="btn btn-primary btn-large btn-disqus" onclick="loadDisqus()"><i class="icon-comments"></i> Show comments</button>
            <button class="btn btn-large btn-disqus" onclick="loadDisqus()" style="display:none"><i class="icon-comments"></i> Hide comments</button>
        </div><!-- End of Disqus Button section -->
        <!-- Disqus thread for the given task -->
        <div id="disqus_thread" style="margin-top:5px;display:none"></div>
    </div><!-- End of Question and Submission DIV (column) -->


Then we will add the code for showing the photos. This second column will be
much simpler:

.. code-block:: html

    <div class="span6"><!-- Start of Photo DIV (columnt) -->
        <a id="photo-link" href="#">
            <img id="photo" src="http://img339.imageshack.us/img339/9017/loadingo.png" style="max-width=100%">
        </a>
    </div><!-- End of Photo DIV (column) -->


In the above code we use a place holder *loadingo.png* that we have created
previously, so we show an image while the first one from the task is getting
loaded.

The second section of the skeleton, if we join the previous snippets of code
will be like this:

.. code-block:: html

    <div class="row skeleton"> <!-- Start Skeleton Row-->
        <div class="span6 "><!-- Start of Question and Submission DIV (column) -->
            <h1 id="question">Question</h1> <!-- The question will be loaded here -->
            <div id="answer"> <!-- Start DIV for the submission buttons -->
                <!-- If the user clicks this button, the saved answer will be value="yes"-->
                <button class="btn btn-success btn-answer" value='Yes'><i class="icon icon-white icon-thumbs-up"></i> Yes</button>
                <!-- If the user clicks this button, the saved answer will be value="no"-->
                <button class="btn btn-danger btn-answer" value='No'><i class="icon icon-white icon-thumbs-down"></i> No</button>
                <!-- If the user clicks this button, the saved answer will be value="NotKnown"-->
                <button class="btn btn-answer" value='NotKnown'><i class="icon icon-white icon-question-sign"></i> I don't know</button>
            </div><!-- End of DIV for the submission buttons -->
            <!-- Feedback items for the user -->
            <p>You are working now on task: <span id="task-id" class="label label-warning">#</span></p>
            <p>You have completed: <span id="done" class="label label-info"></span> tasks from
            <!-- Progress bar for the user -->
            <span id="total" class="label label-inverse"></span></p>
            <div class="progress progress-striped">
                <div id="progress" rel="tooltip" title="#" class="bar" style="width: 0%;"></div>
            </div>
            <!-- 
                This application uses Disqus to allow users to provide some feedback.
                The next section includes a button that when a user clicks on it will
                load the comments, if any, for the given task
            -->
            <div id="disqus_show_btn" style="margin-top:5px;">
                <button class="btn btn-primary btn-large btn-disqus" onclick="loadDisqus()"><i class="icon-comments"></i> Show comments</button>
                <button class="btn btn-large btn-disqus" onclick="loadDisqus()" style="display:none"><i class="icon-comments"></i> Hide comments</button>
            </div><!-- End of Disqus Button section -->
            <!-- Disqus thread for the given task -->
            <div id="disqus_thread" style="margin-top:5px;display:none"></div>
        </div><!-- End of Question and Submission DIV (column) -->
        <div class="span6"><!-- Start of Photo DIV (column) -->
            <a id="photo-link" href="#">
                <img id="photo" src="http://img339.imageshack.us/img339/9017/loadingo.png" style="max-width=100%">
            </a>
        </div><!-- End of Photo DIV (columnt) -->
    </div><!-- End of Skeleton Row -->


2. Loading the Task data
~~~~~~~~~~~~~~~~~~~~~~~~

Now that we have set up the *skeleton* to load the task data, let's see what
JavaScript should we write to populate with the pictures from Flickr and how we
can grab the answer of the user and save it back in the server.

All the action takes place in the file_
**template.html** script section.

The script is very simple, it uses the  `PyBossa.JS library
<http://pybossajs.rtfd.org>`_ to get a new task and
to submit and save the answer in the server.

`PyBossa.JS <http://pybossajs.rtfd.org>`_ provides two methods that have to
been overridden with some logic, as each application will have a different
need, i.e. some applications will be loading other type of data in a different
skeleton:

  * pybossa.taskLoaded(function(task, deferred){});
  * pybossa.presentTask(function(task, deferred){});

The **pybossa.taskLoaded** method will be in charge of adding new **<img/>**
objects to the DOM once they have been loaded from Flickr (the URL is provided
by the task object in the field task.info.url_b), and resolve  the deferred
object, so another task for the current user can be pre-loaded. The code is the
following:

.. code-block:: javascript

    pybossa.taskLoaded(function(task, deferred) {
        if ( !$.isEmptyObject(task) ) {
            // load image from flickr
            var img = $('<img />');
            img.load(function() {
                // continue as soon as the image is loaded
                deferred.resolve(task);
            });
            img.attr('src', task.info.url_b).css('height', 460);
            img.addClass('img-polaroid');
            task.info.image = img;
        }
        else {
            deferred.resolve(task);
        }
    });

The **pybossa.presentTask** method will be called when a task has been obtained
from the server: 

.. code-block:: javascript

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


That JSON object will be accessible via the task object passed as an argument
to the pybossa.presentTask method. First we will need to check that we are not
getting an empty object, as it will mean that there are no more available tasks
for the current user. In that case, we should hide the skeleton, and say thanks
to the user as he has participated in all the tasks of the application.

If the task object is not empty, then we have task to load into the *skeleton*.
In this demo application, we will basically updating the question, adding the
photo to the DOM, updating the user progress and add some actions to the 
submission buttons so we can save the answer of the volunteer.

The PyBossa.JS library treats the user input as an "async function". This is
why the function gets a deferred object, as this object will be *resolved* when
the user clicks in one of the possible answers. We use this approach to load in
the background the next task for the user while the volunteer is solving the
current one. Once the answer has been saved in the server, we resolve the
deferred:

.. code-block:: javascript

    pybossa.presentTask(function(task, deferred) {
        if ( !$.isEmptyObject(task) ) {
            loadUserProgress();
            $('#photo-link').html('').append(task.info.image);
            $("#photo-link").attr("href", task.info.link);
            $("#question").html(task.info.question);
            $('#task-id').html(task.id);
            $('.btn-answer').off('click').on('click', function(evt) {
                var answer = $(evt.target).attr("value");
                if (typeof answer != 'undefined') {
                    //console.log(answer);
                    pybossa.saveTask(task.id, answer).done(function() {
                        deferred.resolve();
                    });
                    $("#loading").fadeIn(500);
                    if ($("#disqus_thread").is(":visible")) {
                        $('#disqus_thread').toggle();
                        $('.btn-disqus').toggle();
                    }
                }
                else {
                    $("#error").show();
                }
            });
            $("#loading").hide();
        }
        else {
            $(".skeleton").hide();
            $("#loading").hide();
            $("#finish").fadeIn(500);
        }
    });

It is important to note that in this method we bind the *on-click* action for
the *Yes*, *No* and *I don't know* buttons to call the above
snippet:

.. code-block:: javascript

    $('.btn-answer').off('click').on('click', function(evt) {
        var answer = $(evt.target).attr("value");
        if (typeof answer != 'undefined') {
            //console.log(answer);
            pybossa.saveTask(task.id, answer).done(function() {
                deferred.resolve();
            });
            $("#loading").fadeIn(500);
            if ($("#disqus_thread").is(":visible")) {
                $('#disqus_thread').toggle();
                $('.btn-disqus').toggle();
            }
        }
        else {
            $("#error").show();
        }
    });


If your application uses other input methods, you will have to adapt this to
fit your application needs.

Finally, the pybossa.presentTask calls a method named
**loadUserProgress**. This method is in charge of getting the user progress of
the user and update the progress bar accordingly:

.. code-block:: javascript

    function loadUserProgress() {
        pybossa.userProgress('flickrperson').done(function(data){
            var pct = Math.round((data.done*100)/data.total);
            $("#progress").css("width", pct.toString() +"%");
            $("#progress").attr("title", pct.toString() + "% completed!");
            $("#progress").tooltip({'placement': 'left'}); 
            $("#total").text(data.total);
            $("#done").text(data.done);
        });
    }

You can update the code to only show the number of answers, or remove it
completely, however the volunteers will benefit from this type of information
as they will be able to know how many tasks they have to do, giving an idea of
progress while the contribute to the project.

Finally, we only need in our application to run the PyBossa application:

.. code-block:: javascript

    pybossa.run('flickrperson')


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
library <http://pybossajs.rtfd.org>`_. In this case:

.. code-block:: javascript

  pybossa.saveTask( taskid, answer )

The *pybossa.saveTask* method saves an answer for a given task. In the
previous section we show that in the pybossa.presentTask method the *task-id*
can be obtained, as we will be passing the object to saveTask method.

The method allows us to give a successful pop-up feedback for the user, so you  
can use the following structure to warn the user and tell him that his answer
has been successfully saved:

.. code-block:: javascript

  pybossa.saveTask( taskid, answer ).done(
    function( data ) {
        // Show the feedback div
        $("#success").fadeIn(); 
        // Fade out the pop-up after a 1000 miliseconds
        setTimeout(function() { $("#success").fadeOut() }, 1000);
    };
  );


2. Updating the template for all the tasks
------------------------------------------

It is possible to update the template of the application without
having to re-create the application and its tasks. In order to update the
template, you only have to modify the file *template.html* and run the following
command::

  python createTasks.py -u http://PYBOSSA-SERVER -k API-KEY -t

You can also use the web interface to do it, and see the changes in real time
before saving the results. Check your application page, and click in the button
**Edit the task presenter**


3. Test the task presenter
--------------------------

In order to test the application task presenter, go to the following URL::

  http://PYBOSSA-SERVER/app/SLUG/presenter

The presenter will load one task, and you will be able to submit and save one
answer for the current task.

4. Check the results
--------------------

In order to see the answers from the volunteers, you can open in your web
browser the file **results.html**. The web page should show a chart pie with
answers from the server http://crowdcrafting.org but you can modify the file
**results.js** to poll your own server data.
¬                                                                                    
The results page shows the number of answers from the volunteers for a given
task (the related photo will be shown), making easy to compare the results
submitted by the volunteers.

The results page is created using the `D3.JS library <http://d3js.org>`_.

.. note::
    You can see a demo of the results page `here
    <http://dev.pybossa.com/app-flickrperson>`_

Creating a tutorial for the users
=================================

In general, users will like to have some feedback when accessing for the very
first time your application. Usually, the overview page of your application
will not be enough, so you can actually build a tutorial (a web page) that
will explain to the volunteer how he can participate in the application.

PyBossa will detect if the user is accessing for the very first time your
application, so in that case, it will load the **tutorial** if your application
has one.

Adding a tutorial is really simple: you only have to create a file named
**tutorial.html** and load the content of the file to the **info** object::

  info = { 'thumbnail': http://hosting-service/thumbnail-name.png,
           'task_presenter': template.html file,
           'tutorial': '<div class="row"><div class="span12"><h1>Tutorial</h1>...</div></div>'
         }

The `createTasks.py <https://github.com/PyBossa/app-flickrperson/blob/master/createTasks.py>`_ 
file will detect if you have file called
**tutorial.html** and in that case, load the contents automatically for you in
the **info** JSON object.

The tutorial could have whatever you like: videos, nice animations, etc.
PyBossa will render for you the header and the footer, so you only have to
focus on the content. You can actually copy the template.html file and use it
as a draft of your tutorial or just include a video of yourself explaining why 
your project is important and how, as a volunteer, you can contribute.

If your application has a tutorial, you can actually access it directly in this
endpoint::

  http://server/app/tutorial
  

.. _export-results:

Exporting the obtained results
================================

You can export all the available tasks and task runs for your application in 
three different ways:

* JSON_, an open standard designed for human-readable data interchange, or 
* CSV_,  a file that stores tabular data (numbers and text) in plain-text form
  and that can be opened with almost any spreadsheet software, or
* CKAN_ web server,  a powerful data management system that makes data accessible
  –by providing tools to streamline publishing, sharing, finding and using
  data.

.. _JSON: http://en.wikipedia.org/wiki/JSON
.. _CSV: http://en.wikipedia.org/wiki/Comma-separated_values
.. _CKAN: http://ckan.org

For exporting the data, all you have to do is to visit the following URL in
your web-browser::

    http://PYBOSSA-SERVER/app/slug/tasks/export

You will find a simple interface that will allow you to export the Tasks and
Task Runs to JSON_ and CSV_ formats:

.. image:: http://i.imgur.com/IAvl9OL.png
    :width: 100%

The previous methods will export all the tasks and task runs, **even if they
are not completed**. When a task has been completed, in other words, when a 
task has collected the number of answers specified by the task 
(**n_answers** = 30 by default), a **brown button** with the text 
**Download results** will pop up, and if you 
click it all the answers for the given task will be shown in JSON format.

You can check which tasks are completed, going to the application URL::

    http://PYBOSSA-SERVER/app/slug

And clicking in the **Tasks** link in the **left local navigation**, and then
click in the **Browse** box:

.. image:: http://i.imgur.com/2Q3x2wP.png
    :width: 100%

Then you will see which tasks are completed, and which ones you can download in
JSON_ format:

.. image:: http://i.imgur.com/hTgkR3U.png

You could download the results
also using the API. For example, you could write a small script that gets the list
of tasks that have been completed using this url::

    GET http://PYBOSSA-SERVER/api/task?state=completed

.. note::
    If your application has more than 20 tasks, then you will need to use the
    **offset** and **limit** parameters to get the next tasks, as by default
    PyBossa only returns the first 20 items.

Once you have obtained the list of completed tasks, your script could start
requesting the collected answers for the given tasks::

    GET http://PYBOSSA-SERVER/api/taskrun?task_id=TASK-ID

.. note::

    If your application is collecting more than 20 answers per task, by default
    PyBossa will be collecting 30, you will need to add the following to the
    query: &limit=n_answers so you can get all the submitted answers by the
    volunteers for the given task.


Exporting the task and task runs in JSON
----------------------------------------

For the JSON_ format, you will get all the output in the web browser, so you
will have to save the created page afterwords:

.. image:: http://i.imgur.com/raRHtmq.png

Exporting the task and task runs to a CSV file
----------------------------------------------

While for the CSV_ format, you will get a CSV file that will be automatically
saved in your computer:

.. image:: http://i.imgur.com/iGPMc9w.png

Exporting the task and task runs to a CKAN server
-------------------------------------------------

If the server has been configured to allow you to export your aplication's data
to a CKAN server (see :ref:`config-ckan`), the owner of the application will see another box that will
give you the option to export the data to the CKAN server.

.. image:: http://i.imgur.com/cAEBjez.png
    :width: 100%

In order to use this method you will need to add the CKAN API-KEY associated
with your account, otherwise you will not be able to export the data and
a warning message will let you know it.

Adding the CKAN API-KEY is really simple. You only need to create an account in
the supported CKAN server (i.e. `the Data hub`_), check your profile and copy
the API-KEY. Then, open your PyBossa account page, edit it and paste the key in
the section **External Services**.

.. image:: http://i.imgur.com/f3gGQji.png

Then, you will be able to actually export the data to the CKAN server and host
it there. Your application will show in the info page at the bottom a link to
your published data in the CKAN server so other people, citizens or researchers
can actually cite your work.

.. image:: http://i.imgur.com/98xjH8a.png

.. _`the Data hub`: http://datahub.io
