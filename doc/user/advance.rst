============================================
ADVANCE: Using the task ID with FlickrPerson
============================================

PyBossa features a new endpoint system that allows every application to load
a specific Task for a given application.

The following URL is available for every application::

  http://pybossa.com/app/slug/task/id

The new endpoint is the same one as the **presenter** one, so the template.html
should take care of using this new endpoint using some JavaScript.

New Work Flow
=============

This new endpoint opens the possibility to use the following work flow:

* Users will load the following page http://pybossa.com/app/newtask
* The template.html JavaScript should check if the window.location.pathname has the following sub-string: task
* If the answer is Yes, then, it should load using an AJAX call the information for the given task
* Else, the pybossa.newTask() method should be used to obtain a task for the user, and change the window.location.href to the new endpoint:

  * pybossa.newTask gets the task.id that the user has to load


Therefore, while this new work flow is more powerful, the owner of the
application will have to code a bit more for loading the tasks in its own URL

Checking if the application has to load a Task or request a new one
===================================================================

The following code shows how any PyBossa application can check if it has to
load a specific task, or request a new one for the user using PyBossa.JS::

  pathArray = window.location.pathname.split('/');
  if (window.location.pathname.indexOf('/task/')!=-1) {
      var l = pathArray.length;
      var i = 0;
      for (i=0;i<l;i++) {
          if (pathArray[i]=='task') {
              loadTask(pathArray[i+1]);
          }
      }
  }
  else {
      pybossa.newTask("flickrperson").done( function( data ) { 
  
          if ( !$.isEmptyObject(data.task) ) {
              window.location.pathname = "/app/flickrperson/task/" + data.task.id;
          }
         else {
              $(".skeleton").hide();
              $("#finish").fadeIn();
          }
      });
  }


The first part, gets the URL pathname and checks if the URL contains the
specific keyword **task**. If the answer is yes, the code will get all the
items from the pathname, calling the function **loadTask(pathArray[i+1])**.

The code checks if after requesting a new Task, nothing is returned, then the
presenter should be shown with a message telling the user that he has
participated in all the available tasks.

Loading the specific task
=========================

Once the application has obtained a task for the user, the function loadTask
will be called::

  function loadTask( task_id ) {
    // Uncomment next line for debugging purposes
    //console.log( data );
    var t = $.ajax({
        url: '/api/task/'+task_id,
        dataType: 'json'
    });
    t.done( function (task) {
        if ( !$.isEmptyObject(task) ) {
            spinnerStart();
            if (task.status=='completed') {
                $('#answer').hide();
                $('#disqus_thread').hide();
                $('#taskcompleted').show();
            }
            $("#question h2").text(task.info.question);
            $("#task-id").text(task.id);
            $("#photo-link").attr("href", task.info.link);
            $("#photo").attr("src", task.info.url_m);
        }
       else {
            $(".skeleton").hide();
            $("#finish").fadeIn();
        }
    });
  }
   
The AJAX call request the task_id and when the call has been **done** the data
will be loaded. The only difference with the previous method, is that this work
flow needs to have the **question** in task.info JSON object, otherwise the
task question will be empty.

Finally, we will have to load a new task after the user has saved the answer.

Requesting a new task after saving an answer
============================================

When the user submits a task, the previous code requested a new task directly
from the same page, however we have to do it in a different way.

Once the answer has been saved, the submitTask(answer) function should change
the pathname again for requesting a new task::

  window.location.pathname = "/app/flickrperson/newtask"

This will trigger the right methods described in the beginning of this section,
checking if the URL has the **task** keyword in the pathname, and acting
accordingly.

With this set of changes, the application will be able to load external tools
like Disqus forums, as each task will have its own URL, so users can talk about
it.
