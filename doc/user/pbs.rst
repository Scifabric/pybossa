======================
Using the command line
======================
In this section we'll learn how we can use the command line to interact with
our project in a PyBossa server, using the command line tool: **pbs**.

.. _pbs:

pbs
===

**pbs** is a very simple command line interface to a PyBossa server. It allows
you to create projects, add tasks (from a CSV or JSON file) with a nice
progress bar, delete them and update the project templates 
(tutorial, task_presenter, and descriptions) all from the command line.

Installation
============

pbs is available in Pypi, so you can install the software with pip:

.. code-block:: bash

    pip install pybossa-pbs

.. note::
    We recommend to use virtual environments to install new Python libraries
    and packages, so please, before installing the pbs command line tool
    consider using a virtual environment.

If you have all the dependencies, the package will be installed and you will be
able to use it from the command line. The command is: **pbs**.


Configuring pbs
===============

By default, pbs does not need a config file, however you will have to specify
for every command the server and your API key in order to add tasks, create
a project, etc, etc. For specifying the server and API key that you want to
use, all you have to do is pass it as an argument:

.. code-block:: bash

    pbs --server http://server.com --apikey yourkey subcommand

If you work with two or more servers, then, remembering all the keys, and
server urls could be problematic, as well as you will be leaving a trace in
your BASH history file. For this reason, pbs has a configuration file where you
can add all the servers that you are working with.

To create the config file, all you have to do is creating a **.pybossa.cfg**
file in your home folder:

.. code-block:: bash

    cd ~
    vim .pybossa.cfg

The file should have the following structure:

.. code-block:: python

    [default]
    server: http://theserver.com
    apikey: yourkey

If you are working with more servers, add another section below it. For
example:

.. code-block:: python

   [default]
   server: http://theserver.com
   apikey: yourkey
   
   [crowdcrafting]
   server: http://crowdcrafting.org
   apikey: yourkeyincrowdcrafting

By default pbs will use the credentials of the default section, so you don't
have to type anything to use those values. However, if you want to do actions
in the other server, all you have to do is the following:

.. code-block:: bash

    pbs --credentials crowdcrafting --help

That command will use the values of the crowdcrafting section.


Creating a project
==================

Creating a project is very simple. All you have to do is create a file named
**project.json** with the following fields:

.. code-block:: js

    {
        "name": "Flickr Person Finder",
        "short_name": "flickrperson",
        "description": "Image pattern recognition",
        "question": "Do you see a real human face in this photo?"
    }

If you use the name **project.json** you will not have to pass the file name
via an argument, as it's the named used by default. Once you have the file
created, run the following command:

.. code-block:: bash

    pbs create_project

That command should create the project. If you want to see all the available
options, please check the **--help** command:

.. code-block:: bash

    pbs create_project --help

Adding tasks to a project
=========================

Adding tasks is very simple. You can have your tasks in two formats:

 * JSON
 * CSV

Therefore, adding tasks to your project is as simple as this command:

.. code-block:: bash

    pbs add_tasks --tasks-file tasks_file.json --tasks-type=json

If you want to see all the available
options, please check the **--help** command:

.. note::

    By default PyBossa servers use a rate limit for avoiding abuse of the
    API. For this reason, you can only do usually 300 requests per every 15
    minutes. If you are going to add more than 300 tasks, pbs will detect it and
    warn you, auto-enabling the throttling for you to respect the limits.
    Please, see :ref:`rate-limiting` for more details.

.. code-block:: bash

    pbs add_tasks --help

Updating project templates
==========================

Now that you have added tasks, you can work in your templates. All you have to
do to add/update the templates to your project is running the following
command:

.. code-block:: bash

    pbs update_project

That command needs to have in the same folder where you are running it, the
following files:

 * template.html
 * long_description.md
 * tutorial.html

If you want to use another template, you can via arguments:

.. code-block:: bash

    pbs update_project --template /tmp/template.html

If you want to see all the available
options, please check the **--help** command:

.. code-block:: bash

    pbs update_project --help

Deleting tasks from a project
=============================

If you need it, you can delete all the tasks from your project, or only one
using its task.id. For deleting all the tasks, all you've to do is run the
following command:

.. code-block:: bash

    pbs delete_tasks

This command will confirm that you want to delete all the tasks and associated
task_runs. 

If you want to see all the available
options, please check the **--help** command:

.. code-block:: bash

    pbs delete_tasks --help
