==========================
Frequently Asked Questions
==========================

.. note::
    If you do not find your question in this section, please send it to us
    directly to *info AT pybossa DOT com*. We will try to help you and add your
    question to the FAQ.

Users
=====
Do I need to create an account to participate in the project?
-------------------------------------------------------------
It depends. The owners of the applications can disable anonymous contributions
(usually due to privacy issues with the data), forcing you to create an account
if you want to contribute to that specific application.


Applications
============
How can I create an application?
--------------------------------
You can create an application using web forms, or if you prefer it using the
API. We recommend you to read the :doc:`user/overview` and :doc:`user/tutorial` 
sections.

Can I disable anonymous contributions?
--------------------------------------
Yes, you can. Check your application settings and toggle the drop down menu:
*Allow Anonymous Contributors* from Yes to No. Check the :ref:`app-details`
for further information.

Can I create *golden tasks*?
----------------------------
Yes, you can. PyBossa has a field for every Task named: *calibration* that will
identify the task as a *golden* task or as we call them as a *calibration
task*. Calibration tasks can be used to weight the answers of the volunteers
(authenticated and anonymous) as you know the answer for those given tasks. For
example, if a user has answered all the calibration tasks correctly you can
give a weight of 1 point to all his/her answers, while if the user only
answered 50% of them correctly, the answers for the rest of the tasks could be
given a weight of 0.5 points.

Can I delete my application and all the task and task runs?
-----------------------------------------------------------
Yes, you can. If you are the owner of the application you can delete the
application, and automatically all the task and associated task runs will be
deleted (**note**: this cannot be undone!). Check the :ref:`app-delete` section
for further details.

Do you provide any statistics about the users for my application?
-----------------------------------------------------------------
Yes, every application has its own statistics page that shows information about
the distribution of answers per type of user, an estimation about how long it
will take to complete all your tasks, the top 5 authenticated and anonymous
users, etc. Check the *Statistics* link in the left local sidebar of your
application.

My application is not getting too much attention, how can it be a *featured* app?
---------------------------------------------------------------------------------
Featured applications are managed by the administrators of the site. Contact
them about this issue, and they will decide about your application.

I have all my data in a CSV file, can I import it?
--------------------------------------------------
Yes, you can. PyBossa supports the CSV format, so all you have to do is upload
your file to a file server like DropBox, copy the public link and paste it in
the importer section. PyBossa also supports Google Drive Spreadsheets, see
:ref:`csv-import` section for further details.

My data is in a Google Doc Spreadsheet, can I import the data into my app?
--------------------------------------------------------------------------
Yes, you can. PyBossa supports the Google Drive Spreadsheets, so make it
public, copy the link and use that link to import it the Google Drive importer
section. See :ref:`csv-import` section for further details.

All my tasks have been completed, how do I download the results to analyze them?
--------------------------------------------------------------------------------
You can export all the data of your application whenever you want. The data can
be exported directly from the *Tasks* section (check the *Tasks* link in the
left sidebar of your application and click in the export box). PyBossa can
export your tasks and task runs (or answers) to a CSV file, JSON format or to
a CKAN server. See the :ref:`export-results` section for further details.

What is a Task Run?
-------------------
A Task Run is a submitted answer sent by one user (authenticated or anonymous)
to one of the tasks of your application. In other words, it is the work done by
one volunteer for one task.

What is the Task Presenter?
---------------------------
The task presenter is the web application that will load the tasks of your
application and present them to the user. It is an HTML + JavaScript
application. See the :ref:`task-presenter` section for further details.

PyBossa
=======
Does PyBossa have an API?
-------------------------
Yes, it does. PyBossa has a :ref:`api` that allows you to create applications,
download results, import tasks, etc. Please see the :ref:`api` section for more
details and the :doc:`user/tutorial` for a full example about how you can use
it.

Is PyBossa open-source?
-----------------------
Yes, it is. PyBossa is licensed under the `GNU Affero general public license
version 3.0`_. 

.. _`GNU Affero general public license version 3.0`: http://www.gnu.org/licenses/agpl-3.0.html

Do you provide application templates or examples apps?
------------------------------------------------------
Yes, we do. You can find several open source application examples that can be
re-used for image/sound pattern recognition problems, geo-coding, PDF transcription, 
etc. Check the official `Git repository`_ for all the available apps.

.. _`Git repository`: http://github.com/PyBossa/


