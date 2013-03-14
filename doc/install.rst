==================
Installing PyBossa
==================

PyBossa is a python web application built using the Flask micro-framework.

Pre-requisites:

  * Python >= 2.7, <3.0
  * A database plus Python bindings for PostgreSQL version 9.1
  * pip for installing python packages (e.g. on ubuntu python-pip)

.. note::

    We recommend to install PyBossa using a `virtualenv`_ as it will create a an
    isolated Python environment, helping you to manage different dependencies and
    versions without having to deal with root permissions in your server machine.

    virtualenv_ creates an environment that has its own installation directories, 
    that doesn't share libraries with other virtualenv environments (and 
    optionally doesn't access the globally installed libraries either).

    
    You can install the software if you want at the system level if you have root
    privileges, however this may lead to broken dependencies in the OS for all your
    Python packages, so if possible, avoid this solution and use the virtualenv_
    solution.

.. _virtualenv: http://pypi.python.org/pypi/virtualenv

Setting things up
=================

Before proceeding to install PyBossa you will need to configure some other
applications and libraries in your system. In this page, you will get a step by
step guide about how to install all the required packages and libraries for
PyBossa using the latest `Ubuntu Server Long Term Support`_ version available at
the moment.

.. _`Ubuntu Server Long Term Support`: https://wiki.ubuntu.com/LTS

Installing git -a distributed version control system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyBossa uses the git_ distributed version control system for handling the
PyBossa server source code as well as the template applications. 

Git_ is a freen and open source distributed version control system designed to
handle everything from small to very large projects with seepd and efficiency.

.. _git: http://git-scm.com/

.. _Git: http://git-scm.com/

In order to install the software, all you have to do is::

    sudo aptitude install git

Installing the PostgreSQL database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PostgreSQL_ is a powerful, open source object-relational database system. 
It has more than 15 years of active development and a proven architecture that 
has earned it a strong reputation for reliability, data integrity, and correctness.

PyBossa uses PostgreSQL_ as the main database for storing all the data, and you
the required steps for installing it are the following::

    sudo aptitude install postgresql-9.1

.. _PostgreSQL: http://www.postgresql.org/


Installing virtualenv (optional, but recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We recommend to install PyBossa using a `virtualenv`_ as it will create a an
isolated Python environment, helping you to manage different dependencies and
versions without having to deal with root permissions in your server machine.

virtualenv_ creates an environment that has its own installation directories, 
that doesn't share libraries with other virtualenv environments (and 
optionally doesn't access the globally installed libraries either).

You can install the software if you want at the system level if you have root
privileges, however this may lead to broken dependencies in the OS for all your
Python packages, so if possible, avoid this solution and use the virtualenv_
solution.

Installing virtualenv_ in the Ubuntu server could be done like this::

    sudo aptitude install python-virtualenv

After installing the software, now you will be able to create independent virtual
environments for the PyBossa installation as well as for the template
applications (see :doc:`user/tutorial`).

Installing the PyBossa Python requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Installing the required libraries for PyBossa is a step that will need to use
some compilers and dev libraries in order to work. Thus, you will need to
install the following packages::

    sudo aptitude install postgresql-server-dev-9.1 python-dev

Then, you are ready to download the code and install the requirements 
(you may wish to create a virtualenv first)::

  # get the source
  git clone --recursive https://github.com/PyBossa/pybossa
  cd pybossa
  # [optional] create virtualenv first
  # cd pybossa/
  # virtualenv env
  # . env/bin/activate
  pip install -e .

.. note::
    Vim_ editor is a very popular text editor in GNU/Linux systems, however it
    may be difficult for some people if you have never used it before. Thus, if
    you want to try another and much simpler editor for editing the
    configuration files you can use the `GNU Nano`_ editor.

Create a settings file and enter your SQLAlchemy DB URI (you can also override
default settings as needed)::

  cp settings_local.py.tmpl settings_local.py
  # now edit ...
  vim settings_local.py

.. _Vim: http://www.vim.org/
.. _`GNU Nano`: http://www.nano-editor.org/


.. note::

  Alternatively, if you want your config elsewhere or with different name::

    cp settings_local.py.tmpl {/my/config/file/somewhere}
    export PYBOSSA_SETTINGS={/my/config/file/somewhere}

Create the alembic config file and set the sqlalchemy.url to point to your
database::

  cp alembic.ini.template alembic.ini
  # now set the sqlalchemy.url ...

Configuring the DataBase
~~~~~~~~~~~~~~~~~~~~~~~~

You need first to add a user to your PostgreSQL_ DB::

    sudo su postgres
    createuser -P tester 

.. note::
    You should use the same user name that you have used in the
    settings_local.py and alembic.ini files.    

After running the last command, you will have to answer to these questions:

* Shall the new role be a super user? Answer **n** (press the **n** key).
* Shall the new role be allowed to create databases? Answer **y** (press the **y** key).
* Shall the new role be allowed to create more new roles? Answer **n** (press the **n** key).

And now, you can create the database::

    createdb pybossa -O tester

Finally, exit the postgresql user::

    exit

Then, populate the database with its tables::

  python cli.py db_create

Run the web server::

  python pybossa/web.py

Open in your web browser the following URL::

  http://localhost:5000

And if you see the following home page, then, your installation has been
completed:

.. image:: http://i.imgur.com/hPtgo6S.png


Migrating the Database Table Structure
======================================

Sometimes, the PyBossa developers add a new column or table to the PyBossa
server, forcing you to carry out a **migration** of the database. PyBossa uses
Alembic_ for performing the migrations, so in case that your production server
need to upgrade the DB structure to a new version, all you have to do is to::

  git pull origin master
  alembic upgrade head


The first command will get you the latest source code of the server, and the
second one will perform the migration.

.. note::
    If you are using the virtualenv_ be sure to activate it before running the
    Alembic_ upgrade command.

.. _Alembic: http://pypi.python.org/pypi/alembic

Enabling a Cache
================

PyBossa comes with a Cache system (based on `flask-cache <http://packages.python.org/Flask-Cache/>`_) 
that it is disabled by default. If you want to start caching some pages of the PyBossa server, you
only have to modify your settings and change the following value from::

    CACHE_TYPE = 'null'

to::

    CACHE_TYPE = 'simple'

The cache also supports other configurations, so please, check the official
documentation of `flask-cache <http://packages.python.org/Flask-Cache/>`_.

.. note::
   **Important**: We highly recommend you to enable the cache, as it will boost
   the performance of the server caching SQL queries as well as page views. If
   you have lots of applications with hundreds of tasks, you should enable it.

