==================
Installing PyBossa
==================

PyBossa is a python web application built using the Flask micro-framework.

Pre-requisites:

  * Python >= 2.6, <3.0
  * A database plus Python bindings for PostgreSQL
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

Install the code and requirements (you may wish to create a virtualenv first)::

  # get the source
  git clone --recursive https://github.com/PyBossa/pybossa
  cd pybossa
  # [optional] create virtualenv first
  # virtualenv ~/{my-virtualenv}
  pip install -e .

Create a settings file and enter your SQLAlchemy DB URI (you can also override
default settings as needed)::

  cp settings_local.py.tmpl settings_local.py
  # now edit ...
  vim settings_local.py

.. note:

  Alternatively, if you want your config elsewhere or with different name::

    cp settings_local.py.tmpl {/my/config/file/somewhere}
    export PYBOSSA_SETTINGS={/my/config/file/somewhere}

Create the alembic config file and set the sqlalchemy.url to point to your
database::

  cp alembic.ini.template alembic.ini
  # now set the sqlalchemy.url ...

Setup the database::

  python cli.py db_create

Run the web server::

  python pybossa/web.py

Open in your web browser the following URL::

  http://localhost:5000

Upgrading
=========

Do::

  alembic upgrade head

Enabling a Cache
================

PyBossa comes with a Cache system (based on `flask-cache <http://packages.python.org/Flask-Cache/>`_) that it is
disabled by default. If you want to start caching some pages of the PyBossa server, you
only have to modify your settings and change the following value from::

    CACHE_TYPE = 'null'

to::

    CACHE_TYPE = 'simple'

The cache also supports other configurations, so please, check the official
documentation of `flask-cache <http://packages.python.org/Flask-Cache/>`_.

Customizing the Layout and Front Page text
==========================================

PyBossa allows you to override two items:

 * **Front Page Text**
 * **Footer**

If you want to override those items, you have to create a folder named
**custom** and place it in the **template** dir. Then for overriding:

 * **The Front Page Text**: create a file named  **front_page_text.html** and write there some HTML.
 * **The Footer**: create a file named  **_footer.html**, and write some HTML.


Google Analytics
================

PyBossa provides an easy way to integrate Google Analytics with your PyBossa
server. In order to enable it you only have to create a file with the name:
**_ga.html** in the **pybossa/template** folder with the Google Tracking code. 
PyBossa will be including your Google Analytics tracking code in every page
since that moment.

The file **_ga.html** should contain something like this::

    <script type="text/javascript">
      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-XXXXXXXX-X']);
      _gaq.push(['_trackPageview']);
    
      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();
    </script>

Google Custom Search
====================

PyBossa provides a simple way to search within the server pages: Google Custom
Search. In order to enable it you will have to apply for a Google Custom Search
API key and then follow the next steps:

 * Copy the Google Custom Search **script** code
 * Create a new file called **_gcs.html** in the templates folder
 * Paste the previous snippet of code (be sure to delete the
   <gcs:search></gcse:search> line from it.
 * Copy the **_gcs_form.html.template** as **_gcs_form.html** and add your key
   in the input field **cx** (you will find a text like XXXXX:YYYY where you
   should paste your key)

The **_gcs.html** file will have something like this::

    <script>
      (function() {
        var cx = 'XXXXX:YYYY';
        var gcse = document.createElement('script'); gcse.type = 'text/javascript'; gcse.async = true;
        gcse.src = (document.location.protocol == 'https:' ? 'https:' : 'http:') +
            '//www.google.com/cse/cse.js?cx=' + cx;
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(gcse, s);
      })();
    </script>

And the **_gcs_form.html** will be like this::

    <form class="navbar-form" style="padding-top:20px;" action="/search">
          <input type="hidden" name="cx" value="partner-pub-XXXXX:YYYYY"/>
          <input type="hidden" name="cof" value="FORID:10" />
          <input type="hidden" name="ie" value="ISO-8859-1" />
          <div class="input-append">
          <input type="text" name="q" size="21" class="input-small" placeholder="Search"  />
          <span class="add-on"><i class="icon-search" style="color:black"></i></span>
          </div>
    </form>

After these steps, your site will be indexed by Google and Google Custom Search
will be working, providing for your users a search tool.

Global Announcements for the users
==================================

Sometimes you will need to send a message to all your users while they are
browsing the server. For example, an scheduled shutdown for installing new
hardware.

PyBossa provides a general solution for these announcements via the
`settings_local.py.tmpl <https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl>`_ 
configuration file. The announcement feature allows
you to send messages to the following type of users:

 * **Authenticated users**, basically all the registered users in the server.
 * **Admin users**, all the users that are admins/root in the server.
 * **Application owners**, all the users that have created one or more
   applications in the server.

Therefore, let's say that you want to warn all your admins that a new
configuration will be deployed in your system. In this case, all you have to do
is to modify the **ANNOUNCEMENT** variable to display the message for the given
type of users:

.. code-block:: python
    
    ANNOUNCEMENT = {'root': 'Your secret message'}
    

There is an example of the **ANNOUNCEMENT** variable in the
`settings_local.py.tmpl <https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl>`_ 
file, so you can easily adapt it for your own server. Basically, the
announcement variable has a **key** and an associated **message**. The
supported keys are:

 * **admin**: for admin users
 * **user**: for all the registered users (even admins)
 * **owner**: for all registered users that have one or more applications

.. note::
    
    You can use a mix of messages at the same time without problems, so for
    example you can display a message for Admins and Owners at the same time.
