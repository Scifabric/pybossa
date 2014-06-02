=======================
Configuring the Project
=======================

If you are the owner of a project, you can configure it using the web
interface. When you are the owner (also an administrator of the PyBossa server) a new 
link in the left local navigation bar of the project will appear with the
name **Settings**.

.. image:: http://i.imgur.com/IiB0sMG.png
    :width: 100%

The **Settings** page will give you three basic options:

#. :ref:`app-details`: here you will be able to change the name
   of the project, the description, icon, etc.
#. :ref:`task-settings`: this button will open the :ref:`task-settings` page where you
   will be able to configure the :ref:`task-scheduler`, change the
   :ref:`task-priority`, modify the
   :ref:`task-redundancy` 
   and :ref:`delete-tasks` and its associated task runs (also known as
   answers).
#. :ref:`app-delete`: if you click in this button you will be able to
   completely remove the project from the system. A big warning message
   will be shown before allowing you to delete the project.

.. _app-details:

Edit the project details
============================

In this section you can change the following parameters of your project:

* **Name**: the name of the project.
* **Short name**: (also known as *slug*) the string that will be used to access
  your project, http://server/app/short_name.
* **Description**: the short description text of the project.
* **Icon link**: the URL of the icon of the project.
* **Allow Anonymous Contributors**: force users to sign in, in order to
  participate in your project. By default anonymous users are allowed to
  participate in all the projects, so change the value to *No* if you want
  to disable anonymous contributions.
* **Long Description**: change the text (you can use `Markdown`) describing
  the goals of your project.
* **Hide**: tick this field, if you want to hide the project from the
  public listings. You will be the only one with access to it (except admin
  users).

.. image:: http://i.imgur.com/LemKrKJ.png
    :width: 100%

.. _`Markdown`: http://daringfireball.net/projects/markdown/

.. _task-settings:

Task Settings
=============

The *Task Settings* is only accessible for the project owner and server
administrators. The page can be reached via the **Settings** menu, but also
from the **Tasks** link in the left local navigation bar. 

.. image:: http://i.imgur.com/znVy3ON.png
    :width: 100%

The page shows four different blocks:

#. **Task Scheduler**: this block allows you to specify how the project
   should send tasks to the volunteers.
#. **Task Priority**: this block allows you to change the priority of the tasks.
#. **Task Redundancy**: use this block to change the default number of answers
   (30 by default) that you want to obtain before marking a task as completed.
#. **Delete Tasks**: this final block allows you to flush all the tasks and its
   associated task runs (answers).

.. _task-scheduler:

Task Scheduler
--------------

PyBossa provides different task scheduler that will send tasks to the users in
very different ways. 

.. image:: http://i.imgur.com/1KeSido.png
    :width: 100%

Default or Depth First
~~~~~~~~~~~~~~~~~~~~~~

The Default task scheduler (also known as Depth First) has the following
features:

#. It sends the tasks in the order that were created, first in first out.
#. Users (anonymous and authenticated) will only be allowed to participate once
   in the same task. Once a user has submitted a Task Run (or answer) for
   a given task, the scheduler will never send that task to the same user.
#. It will send the same task until the :ref:`task-redundancy` is achieved. In
   other words, if a task has a redundancy value of 3, the task will be always
   sent until those 3 answers have been submitted. Once the 3 answers have been
   collected, the task will be marked as *completed* and it will not be sent
   again.
#. When a user has submitted a Task Run for a given task, the scheduler
   will send to the same user the next task.

In summary, from the point of view of a user (authenticated or anonymous) the
system will be sending the project tasks in the order they were created. If
the user tries to reload a task that he or she already participated, the system
will detect it, and warn the user giving the option to try with another task
(the scheduler will search for the proper task for the given user).

From the point of view of the project, the scheduler will be trying to
complete (get all the answers requested by the :ref:`task-redundancy` value) all
the tasks as soon as possible.

Breadth First
~~~~~~~~~~~~~

The Breadth First scheduler has the following features:

#. It sends the tasks in the order that were created, first in first out.
#. It ignores the :ref:`task-redundancy` value, so it will keep sending tasks
   no matter even though that value has been achieved.
#. It sends always the task with the least number of task runs in the system.
#. A task will be never marked as completed, as the :ref:`task-redundancy` is
   not respected.

In summary, from the point of view of a user (authenticated or anonymous) the
system will be sending the project's tasks that have less answers (in case of
not having an answer, the creation time will be used to send them like in
a FIFO --first in first out). 

From the point of view of the project, the scheduler will be trying to obtain 
as soon as possible an answer for all the available tasks. 

.. note::

    If your project needs to do an statistical analysis, be sure to check if
    the answer has been submitted by the same user, and how many answers you have
    obtained per task.

Random
~~~~~~

The Random scheduler has the following features:

#. It sends a task randomly to the users.
#. A user (authenticated or anonymous) can receive the same task two or more
   times in a row.
#. It ignores the :task:`task-redundancy` value, so tasks will be never marked
   as *completed*.

In summary, from the point of view of a user (authenticated or anonymous) the
system will be sending tasks randomly as the user could receive in a row the
same task several times. 

From the point of view of the project, the scheduler will be sending tasks
randomly.

.. note::
    By using this scheduler, you may end up with some tasks that receive only
    a few answers. If you want to avoid this issue, change to the other two
    schedulers.

.. _task-priority:

Task Priority
--------------

PyBossa allows you to prioritize the tasks, or in other words, which tasks
should be delivered first to the volunteers.

.. image:: http://i.imgur.com/gay8VAw.png
    :width: 100%

.. note::
    **Important**: Task Priority is only respected by the default scheduler.

The page shows you two input boxes:

#. **Task IDs**: comma separated Task IDs of your project tasks. Note: not
   spaces between the values or commas.
#. **Priority**: the priority that you want to set for the Task IDs. This must
   be a value between 0.0 and 1.0.

A task with a priority 1.0 will be the first Task to be delivered to a given
user. In case that two or more tasks have the same priority value, the first task
that will be delivered will be the one with the lower Task.ID value.

.. _task-redundancy:

Task Redundancy
---------------

The Task Redundancy is a feature that will allow you to analyze statistically
the results that your project are getting for each of its tasks.

PyBossa by default assigns a value of 30 task runs --answers-- per task, as
this value is commonly used for analyzing the population statistically.

This page will allow you to change the default value, 30, to whatever you like
between a minimum of 1 or a maximum of 10000 answers per task. We recommend to
have at use at least 3 answers per task, otherwise you will not be able to run
a proper analysis on a given task if two uses answer different. 

.. image:: http://i.imgur.com/rDrG8Bp.png
    :width: 100%

For example, imagine that the goal of the task is to answer if you see a human 
in a picture, and the available answers are Yes and No. If you set up the
redundancy value to 2, and two different users answer respectively Yes and No,
you will not know the correct answer for the task. By increasing the redundancy
value to 5 (or even bigger) you will be able to run a statistical analysis more
accurately.

.. _delete-tasks:

Delete Tasks
------------

This section will allow you to complete remove all the Tasks and associated
Task Runs (answers) of your project.

.. image:: http://i.imgur.com/VmUeaWq.png
    :width: 100%

.. note::
    This step cannot be undone, once you delete all the tasks and associated
    task runs they will be lost forever.

This feature is useful when you are testing your project, and you are
deciding the structure that you are going to build in your answers. 

.. _app-delete:

Delete the project
==================

In case that you want to completely remove the project and all its tasks
and task runs, use this section to delete the project.

.. image:: http://i.imgur.com/Et4EAyj.png
    :width: 100%

.. note::
    This action cannot be undone, so be sure before proceeding.
