================
Project Tutorial
================

This tutorial is based in the demo project **Flickr Person** (`source code`_) provided with
PyBossa. This demo project is a simple microtasking project where users have to
answer the following question: *Do you see a human face in this photo?* The possible
answers are: *Yes, No* and *I don't know*.

.. _source code: https://github.com/PyBossa/app-flickrperson

The demo project Flickr Person has two main components:

  * The :ref:`task-creator` a Python script that creates the tasks in PyBossa, and
  * the :ref:`task-presenter`: an HTML + Javascript structure that will show the tasks 
    to the users and save their answers.

This tutorial uses the PyBossa :ref:`pbs` command line tool.


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
project in PyBossa (only authenticated users can create projects and
tasks, while everyone can collaborate solving the tasks).

.. note::

    The Flickr Person Finder demo project uses :ref:`pbs` 
    that need to be installed in your system before proceeding. For this
    reason, we recommend you to configure a `virtualenv`_  for the project 
    as it will create an isolated Python environment in a folder, 
    helping you to manage different dependencies and
    versions without having to deal with root permissions in your computer.

    virtualenv_ creates an environment that has its own installation directories, 
    that doesn't share libraries with other virtualenv environments (and 
    optionally doesn't access the globally installed libraries either).
    
    You can install the software if you want at the system level if you have root
    privileges, however this may lead to broken dependencies in the OS for all your
    Python packages, so if possible, use only the virtualenv_
    solution.

.. _virtualenv: http://pypi.python.org/pypi/virtualenv


.. note:: 

    Flickr Person Finder uses the **pbs** command line tool which simplifies a lot
    accessing the PyBossa API endpoints. Therefore, you will need to
    install the *pybossa-pbs* with `pip --a python installer packager <http://pypi.python.org/pypi/pip>`_::

    $ pip install pybossa-pbs

.. note::
    
    If you need to install **pip** in your system, check `the official
    documentation. <http://www.pip-installer.org/en/latest/installing.html>`_

Creating the Project
====================

There are two possible methos for creating a project:

  * :ref:`web-interface`: click in your user name, and you will
    see a section named **projects** list. In that section you will be able
    to create a project using the web interface.
  * :ref:`api-interface`: using the **pbs** command line tool.

For this tutorial we are going to use the second option, the :doc:`../api` via
the PyBossa :ref:`pbs` command line tool for interacting with the API.

For creating the project, you will need to parameters

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
so you will have a local copy of the required files to create the project
and tasks using the API.

.. image:: http://i.imgur.com/CYPnPft.png

If you are new to Github and the GIT software, we recommend you to take this
`free and on-line course <http://try.github.com>`_ (it will take you only
15 minutes!) where you will learn the basics, which are the main concepts that
you will need for cloning the demo project repository.

If you prefer to skip the course and take it in a later stage, the commands
that you need to clone the repository are:

.. code-block:: bash

    git clone git://github.com/PyBossa/app-flickrperson.git

After running that command a new folder named **app-flickrperson** will be
created from where you run the command. 

Configuring the name, short name, thumbnail, etc.
=================================================

The Flickr Person Finder provides a file called: `project.json <https://github.com/PyBossa/app-flickrperson/blob/master/project.json>`_  that has the
following content:

.. code-block:: js

    {
        "name": "Flickr Person Finder",
        "short_name": "flickrperson",
        "description": "Image pattern recognition",
    }

You will need to modify the **name** and **short_name** fields in order to
create a project in crowdcrafting.org, as there is already a project
registered with those values. Otherwise, you can keep the same values.

.. note::

    The **name** and **short_name** of the project **must be unique**!
    Otherwise you will get an error (IntegrityError) when creating the project.

You can re-use the other fields if you want. **Description** will be the text
shown in the project listing page. It's important that you try to have a short
description that explains what your project does.

Now that we have the **project.json** file ready, we can create the project:

.. code-block:: bash
    
    pbs --server server --apikey key create_project

This command will read the values in the file **project.json** and it will use
them to create an empty project in the PyBossa server of your choice.

.. note::

    You can save some typing if you create a config file for pbs. Please, check
    the :ref:`pbs` page for more details.

If you want to check if the project exists, just open your web browser, and
type in the folling URL::

    http://server/app/short_name

Where **short_name** is the value of the key with the same name in the file:
**project.json**. You sould get a project page, with not so much information,
as we only have created it. Let's add some tasks to the project.

Adding tasks to the project
===========================

Now that we have the project created, we can add some tasks to our project.
PyBossa will deliver the tasks for the users (authenticated and anonymous ones) 
and store the submitted answers in the PyBossa data base, so you can process
them in a later stage.

A PyBossa task is a JSON object with the information that needs to be processed
by the volunteers. Usually it will be a link to a media file (image, video,
sound clip, PDF file, etc.) that needs to be processed.

While PyBossa internally uses JSON for storing the data, you can add tasks to
your project using two different formats::

 * CSV: a comma separated spreadsheet
 * JSON: a lightweight data-interchange format.

The demo project comes with a CSV sample file, that has the following
structure::

    question, url_m, link, url_b
    Do you see a human face in this photo?, http://srv/img_m.jpg, http://srv/img, http://srv/img_b.jp

Additionally there is a script named: **get_images.py** that will contact
Flickr, get the latest published photos to this web service, and save them in
JSON format as a file (flickr_tasks.json), with the same structure as the CSV file 
(the keys are the same):

.. code-block:: js

  { 'link': 'http://www.flickr.com/photos/teleyinex/2945647308/',
    'url_m': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_m.jpg', 
    'url_b': 'http://farm4.staticflickr.com/3208/2945647308_f048cc1633_b.jpg' }

.. note::

    Flickr creates from the original image different cropped versions of the
    image. It uses a pattern to distinguish them: **_m** for medium size,
    and **_b** for the big ones. There are more options, so if you need more
    help in this matter, check the official `Flickr documentation <http://www.flickr.com/services/api/>`_.

All those keys will be saved into the task field **info** of the task model.

.. note::
    From now own, the tutorial assumes that you have configured your pbs
    installation with a .pybossa.cfg file. Please, see :ref:`pbs` for more
    information.

As we have a CSV file with some tasks, let's use it for adding some tasks to
our project. For adding tasks in CSV format all you have to do is the
following:

.. code-block:: bash

    pbs add_tasks --tasks-file flickr_tasks.csv --tasks-type=csv

After running this program, you will see a progress bar that will let you know
when all the tasks will be added to your project.

Finally, we'll also add some tasks in JSON format using the **get_images.py**
script, that will generate for us the **flickr_tasks.json** file with the last
20 published photos in Flickr. First, we need to create the tasks file:

.. code-block:: bash
    
    python get_images.py

This will create the file: **flickr_tasks.json**. Now, let's add them to our
project:

.. code-block:: bash

    pbs add_tasks --tasks-file flickr_tasks.json --tasks-type=json

Done! Again, a progress bar will show us how long it takes to add all the
tasks. Once it's completed, we can actually move to the next step on the
tutorial: presenting the tasks to the volunteers.

.. note::
    You can check all the available options for the command line with the
    **--help** argument.

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

.. note::
    Since version 2.0.1 PyBossa enforces API Rate Limiting, so you might exceed
    the number of allowed requests, getting a 429 error. Please see
    :ref:`rate-limiting` section.


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
the data when you will analyze it, you can specify it with the pbs command. For
example, in order to reduce the number of users that will analyze each task to
ten, run the following:

.. code-block:: bash

    pbs add_tasks --tasks-file file --tasks-type=type --redundancy 10

In this case the **n_answers** field will make :ref:`task-scheduler` to try and 
obtain 10 different answers from different users for each task in the file.


Changing the Priority of the tasks
==================================

Every task can have its own **priority**. The :ref:`task-priority` can be configured using
the web interface, or the API.

A task with a higher priority will be delivered first to the volunteers. Hence if you 
have a project where you need to analyze a task first due
to an external event (a new data sample has been obtained), then you can modify 
the priority of the new created task and deliver it first. 

If you have a new batch of tasks that need to be processed before all the
available ones, you can do it with pbs. Run the following command:

.. code-block:: bash

    pbs add_tasks --tasks-file file --tasks-type=type --priority 1


The priority is a number between 0.0 and 1.0. The highest priority is 1.0 and
the lowest is 0.0. 

Presenting the Tasks to the user
================================

In order to present the tasks to the user, you have to create an HTML template.

The template is the skeleton that will be used to load the data of the tasks:
the question, the photos, user progress, input fields & submit buttons 
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

This template file will be used by the :ref:`pbs` command line tool to add the
task presenter to the project. You can add it running the following command:

.. code-block:: bash

    pbs update_project

.. note::
    You can also edit the HTML skeleton using the web interface. Once the
    project has been created in PyBossa you will see a button that allows
    you to edit the skeleton using a WYSIWYG editor.

In PyBossa every project has a **presenter** endpoint:

 * http://PYBOSSA-SERVER/app/SLUG/newtask

.. note::
   The **slug** is the short name for the project, in this case 
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
            <a class="btn small" href="/app">or, Check other projects</a>
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
            This project uses Disqus to allow users to provide some feedback.
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
                This project uses Disqus to allow users to provide some feedback.
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
------------------------

Now that we have set up the *skeleton* to load the task data, let's see what
JavaScript should we write to populate with the pictures from Flickr and how we
can grab the answer of the user and save it back in the server.

All the action takes place in the file_
**template.html** script section.

The script is very simple, it uses the  `PyBossa.JS library
<http://pybossajs.rtfd.org>`_ to get a new task and
to submit and save the answer in the server.

`PyBossa.JS <http://pybossajs.rtfd.org>`_ provides two methods that have to
been overridden with some logic, as each project will have a different
need, i.e. some projects will be loading other type of data in a different
skeleton:

  * pybossa.taskLoaded(function(task, deferred){});
  * pybossa.presentTask(function(task, deferred){});

The **pybossa.taskLoaded** method will be in charge of adding new **<img/>**
objects to the DOM once they have been loaded from Flickr (the URL is provided
by the task object in the field task.info.url_b), and resolve  the deferred
object, so another task for the current user can be pre-loaded. The code is the
following:

.. code-block:: js

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

.. code-block:: js

  { question: project.description,
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
to the user as he has participated in all the tasks of the project.

If the task object is not empty, then we have task to load into the *skeleton*.
In this demo project, we will basically updating the question, adding the
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


If your project uses other input methods, you will have to adapt this to
fit your project needs.

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

Finally, we only need in our application to run the PyBossa project:

.. code-block:: javascript

    pybossa.run('flickrperson')


3. Saving the answer
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


4. Updating the template for all the tasks
------------------------------------------

It is possible to update the template of the project without
having to re-create the project and its tasks. In order to update the
template, you only have to modify the file *template.html* and run the following
command:

.. code-block:: bash

    pbs update_project

You can also use the web interface to do it, and see the changes in real time
before saving the results. Check your project page, go to the tasks section,
and look for the **Edit the task presenter** button.


5. Test the task presenter
--------------------------

In order to test the project task presenter, go to the following URL::

  http://PYBOSSA-SERVER/app/SLUG/presenter

The presenter will load one task, and you will be able to submit and save one
answer for the current task.


6. Check the results
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
first time your project. Usually, the overview page of your project
will not be enough, so you can actually build a tutorial (a web page) that
will explain to the volunteer how he can participate in the project.

PyBossa will detect if the user is accessing for the very first time your
project, so in that case, it will load the **tutorial** if your project
has one.

Adding a tutorial is really simple: you only have to create a file named
**tutorial.html** and load the content of the file using pbs:

.. code-block:: bash

    pbs update_project

The tutorial could have whatever you like: videos, nice animations, etc.
PyBossa will render for you the header and the footer, so you only have to
focus on the content. You can actually copy the template.html file and use it
as a draft of your tutorial or just include a video of yourself explaining why
your project is important and how, as a volunteer, you can contribute.

If your project has a tutorial, you can actually access it directly in this
endpoint::

  http://server/app/tutorial


Providing some I18n support
===========================

Sometimes, you may want to give the users of your project a little help and
present them the tutorial and tasks in their language. To allow this, you can
access their locale via Javascript in a very easy way, as we've placed it in a
hidden 'div' node so you can access it just like this:

.. code-block:: javascript

    var userLocale = document.getElementById('PYBOSSA_USER_LOCALE').textContent.trim();


The way you use it after that is up to you. But let's see an example of how you
can use it to make a tutorial that automatically shows the strings in the locale
of the user.

.. note::
    Anonymous users will be only shown with **en** language by default. This
    feature only works for authenticated users that choose their own locale in
    their account. You can however, load the translated strings using the
    browser preferred language.

First of all, check the *tutorial.html file*. You will see it consists on some
HTML plus some Javascript inside a <script> tag to handle the different steps of
the tutorial. Here you have a snippet of HTML tutorial file: 

.. code-block:: html

    <div class="row">
        <div class="col-md-12">
            <div id="modal" class="modal hide fade">
                <div class="modal-header">
                    <h3>Flickr Person Finder tutorial</h3>
                </div>
                <div id="0" class="modal-body" style="display:none">
                    <p><strong>Hi!</strong> This is a <strong>demo project</strong> that shows how you can do pattern recognition on pictures or images using the PyBossa framework in Crowdcrafting.org.
                   </p>
                </div>
                <div id="1" class="modal-body" style="display:none">
                    <p>The application is really simple. It loads a photo from <a href="http://flickr.com">Flickr</a> and asks you this question: <strong>Do you see a human in this photo?</strong></p>
                    <img src="http://farm7.staticflickr.com/6109/6286728068_2f3c6912b8_q.jpg" class="img-thumbnail"/>
                    <p>You will have 3 possible answers:
                    <ul>
                        <li>Yes,</li>
                        <li>No, and</li>
                        <li>I don't know</li>
                    </ul>
                    </p>
                    <p>
                    </p>
                    <p>All you have to do is to click in one of the three possible answers and you will be done. This demo project could be adapted for more complex pattern recognition problems.</p>
                </div>
                <div class="modal-footer">
                    <a id="prevBtn" href="#" onclick="showStep('prev')" class="btn">Previous</a>
                    <a id="nextBtn" href="#" onclick="showStep('next')" class="btn btn-success">Next</a>
                    <a id="startContrib" href="../flickrperson/newtask" class="btn btn-primary" style="display:none"><i class="fa fa-thumbs-o-up"></i> Try the demo!</a>
                </div>
            </div>
        </div>
    </div>

To add multilingual support, copy and paste it is as many times as languages
you're planning to support.

Then, add to each of them an id in the most outer 'div' which corresponds to the
abreviated name of the locale ('en' for English, 'es' for Spanish, etc.), and
translate the inner text of it, but leave all the HTML the same in every
version (tags, ids, classes, etc.) like:

.. code-block:: html

    <div id='es' class="row">
       Your translated version of the HTML goes here, but only change the text,
       NOT the HTML tags, IDs or classes.
    </div>

Finally, in the Javascript section of the tutorial, you will need to add some
extra code to enable multilingual tutorials. Thus, modify the javascript from:

.. code-block:: javascript

    var step = -1;
    function showStep(action) {
        $("#" + step).hide();
        if (action == 'next') {
            step = step + 1;
        }
        if (action == 'prev') {
            step = step - 1;
        }
        if (step == 0) {
            $("#prevBtn").hide();
        }
        else {
            $("#prevBtn").show();
        }

        if (step == 1 ) {
            $("#nextBtn").hide();
            $("#startContrib").show();
        }
        $("#" + step).show();
    }

    showStep('next');
    $("#modal").modal('show');

To:

.. code-block:: javascript

    var languages = ['en', 'es']
    $(document).ready(function(){
        var userLocale = document.getElementById('PYBOSSA_USER_LOCALE').textContent.trim();
        languages.forEach(function(lan){
            if (lan !== userLocale) {
                var node = document.getElementById(lan);
                if (node.parentNode) {
                    node.parentNode.removeChild(node);
                }
            }
        });
        var step = -1;
        function showStep(action) {
            $("#" + step).hide();
            if (action == 'next') {
                step = step + 1;
            }
            if (action == 'prev') {
                step = step - 1;
            }
            if (step == 0) {
                $("#prevBtn").hide();
            }
            else {
                $("#prevBtn").show();
            }

            if (step == 1 ) {
                $("#nextBtn").hide();
                $("#startContrib").show();
            }
            $("#" + step).show();
        }
        showStep('next');
        $("#modal").modal('show');
    });

Notice the languages array variable defined at the beggining?. It's important
that you place there the ids you've given to the different translated versions
of your HTML for the tutorial. The rest of the script will only compare the
locale of the user that is seeing the tutorial and delete all the HTML that is
not in his language, so that only the tutorial that fits his locale settings is
shown.

Another method to support I18n
------------------------------

Another option for translating your project to different languages is using
a JSON object like this:

.. code-block:: javascript

    messages = {"en": 
                   {"welcome": "Hello World!,
                    "bye": "Good bye!"
                   },
                "es:
                   {"welcome": "Hola mundo!",
                    "bye": "Hasta luego!"
                   }
               }

This object can be placed in the *tutorial.html* or *template.html* file to
load the proper strings translated to your users.

The logic is very simple. With the following code you grab the language that
should be loaded for the current user:

.. code-block:: javascript

    var userLocale = document.getElementById('PYBOSSA_USER_LOCALE').textContent.trim();


Now, use userLocale to load the strings. For example, for *template.html* and
the Flickrperson demo project, you will find the following code at the start of
the script:

.. code-block:: javascript

    // Default language
    var userLocale = "en";
    // Translations
    var messages = {"en": {
                            "i18n_welldone": "Well done!",
                            "i18n_welldone_text": "Your answer has been saved",
                            "i18n_loading_next_task": "Loading next task...",
                            "i18n_task_completed": "The task has been completed!",
                            "i18n_thanks": "Thanks a lot!",
                            "i18n_congratulations": "Congratulations",
                            "i18n_congratulations_text": "You have participated in all available tasks!",
                            "i18n_yes": "Yes",
                            "i18n_no_photo": "No photo",
                            "i18n_i_dont_know": "I don't know",
                            "i18n_working_task": "You are working now on task:",
                            "i18n_tasks_completed": "You have completed:",
                            "i18n_tasks_from": "tasks from",
                            "i18n_show_comments": "Show comments:",
                            "i18n_hide_comments": "Hide comments:",
                            "i18n_question": "Do you see a human face in this photo?",
                          },
                    "es": {
                            "i18n_welldone": "Bien hecho!",
                            "i18n_welldone_text": "Tu respuesta ha sido guardada",
                            "i18n_loading_next_task": "Cargando la siguiente tarea...",
                            "i18n_task_completed": "La tarea ha sido completadas!",
                            "i18n_thanks": "Muchísimas gracias!",
                            "i18n_congratulations": "Enhorabuena",
                            "i18n_congratulations_text": "Has participado en todas las tareas disponibles!",
                            "i18n_yes": "Sí",
                            "i18n_no_photo": "No hay foto",
                            "i18n_i_dont_know": "No lo sé",
                            "i18n_working_task": "Estás trabajando en la tarea:",
                            "i18n_tasks_completed": "Has completado:",
                            "i18n_tasks_from": "tareas de",
                            "i18n_show_comments": "Mostrar comentarios",
                            "i18n_hide_comments": "Ocultar comentarios",
                            "i18n_question": "¿Ves una cara humana en esta foto?",
                          },
                   };
    // Update userLocale with server side information
     $(document).ready(function(){
         userLocale = document.getElementById('PYBOSSA_USER_LOCALE').textContent.trim();
    
    });
    
    function i18n_translate() {
        var ids = Object.keys(messages[userLocale])
        for (i=0; i<ids.length; i++) {
            console.log("Translating: " + ids[i]);
            document.getElementById(ids[i]).innerHTML = messages[userLocale][ids[i]];
        }
    }

First, we define the default locale, "en" for English. Then, we create
a messages dictionary with all the ids that we want to translate. Finally, we
add the languages that we want to support.

.. note::
    
    PyBossa will give you only the following 3 locale settings: "en", "es" and
    "fr" as PyBossa is only translated to those languages. If you want to add
    another language, please, help us to translate PyBossa (see
    :ref:`translating`).


As you can see, it's quite simple as you can share the messages object with
your volunteers, so you can get many more translations for your project easily.

Finally, we need to actually load those translated strings into the template.
For doing this step, all we've to do is adding the following code to our
*template.html* file at the function pybossa.presentTask:

.. code-block:: javascript

    pybossa.presentTask(function(task, deferred) {
        if ( !$.isEmptyObject(task) ) {
            loadUserProgress();
            i18n_translate();
            ...

Done! When the task is loaded, the strings are translated and the project will
be shown in the user language.


Providing more details about the project
========================================

Up to now we have created the project, added some tasks, but the project still
lacks a lot of information. For example, a welcome page (or long description)
of the project, so the users can know what this project is about.

If you check the source code, you will see that there is a file named
*long_description.md*. This file has a long description of the project,
explaining different aspects of it.

This information is not mandatory, however it will be very useful for the users
as they will get a bit more of information about the project goals.

The file can be composed using Markdown or plain text.

The long description will be shown in the project home page::

 http://crowdcrafting.org/app/flickrperson

If you want to modify the description you have two options, edit it via the web
interface, or modify locally the *long_description.md* file and run pbs to
update it:

.. code-block:: bash

    pbs update_project
    

Adding an icon to the project
=============================

It is possible also to add a nice icon for the project. By default PyBossa
will render a 100x100 pixels empty thumbnail for those projects that do not
provide it. 

If you want to add an icon you can do it by using the web interface. Just go to
the **Settings** tab within your project. There, select the image file you
want to use and push the **Upload** button. That's all!


Protecting the project with a password
======================================

If, for any reason, you want to allow only certain people to contribute to your
project, you can set a password. Thus, every time a user (either anonymous or
authenticated) wants to contribute to the project, it will be asked to introduce
the password. The user will then be able to contribute to the project for 30
minutes (this is a value by default, can be changed in every PyBossa server).
After this time, the user will be asked again to introduce the password if wants
to continue contributing, and so on.


Creating a blog for the project
===============================

You can share the progress of the project creating a blog. Every PyBossa
project includes a very simple blog where you will be able to write about
your project regularly.

You can use Markdown or plain text for the content of the posts. And you will
also be able to edit them or delete after creation if you want.

To write a post simply go to the project **Settings tab and there you will
find an option to write, read or delete your blog posts.


.. _export-results:

Exporting the obtained results
================================

You can export all the available tasks and task runs for your project in 
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

You can check which tasks are completed, going to the project URL::

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
    If your project has more than 20 tasks, then you will need to use the
    **offset** and **limit** parameters to get the next tasks, as by default
    PyBossa API only returns the first 20 items.

Once you have obtained the list of completed tasks, your script could start
requesting the collected answers for the given tasks::

    GET http://PYBOSSA-SERVER/api/taskrun?task_id=TASK-ID

.. note::

    If your project is collecting more than 20 answers per task, then you will
    need to use the **offset** and **limit** parameters to get the next task
    runs, as by default PyBossa API only returns the first 20 items. That way
    you will be able to get all the submitted answers by the volunteers for the
    given task.


Exporting the task and task runs in JSON
----------------------------------------

For the JSON_ format, you will get all the output as a file that your browser
will download, named: short_name_tasks.json for the tasks, and
short_name_task_runs.json for the task runs.


Exporting the task and task runs to a CSV file
----------------------------------------------

While for the CSV_ format, you will get a CSV file that will be automatically
saved in your computer:

.. image:: http://i.imgur.com/iGPMc9w.png

Exporting the task and task runs to a CKAN server
-------------------------------------------------

If the server has been configured to allow you to export your aplication's data
to a CKAN server (see :ref:`config-ckan`), the owner of the project will see another box that will
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

.. image:: http://i.imgur.com/nYw9rcj.png

Then, you will be able to actually export the data to the CKAN server and host
it there. Your project will show in the info page at the bottom a link to
your published data in the CKAN server so other people, citizens or researchers
can actually cite your work.

.. image:: http://i.imgur.com/98xjH8a.png

.. _`the Data hub`: http://datahub.io
