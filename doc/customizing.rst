===================
Configuring PyBossa
===================

The PyBossa `settings_local.py.tmpl`_ file has all the available configuration
options for your server. This section, explains each of them and how you
should/could use them in your server.

.. _`settings_local.py.tmpl`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl

Debug mode
==========

The DEBUG_ mode is disabled by default in the configuration file, as this should
be only used when you are running the server for development purposes. You
should not enable this option, unless you need to do some debugging in the
PyBossa server

.. _DEBUG: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L1

.. note::
    For further details about the DEBUG mode in the PyBossa server, please,
    check the official documentation_.

.. _documentation: http://flask.pocoo.org/docs/quickstart/#debug-mode

Host and Port
=============

The HOST_ and PORT_ config variables can be used to force the server to listen
in specific addresses of your server, as well as at a given port. Usually, you
will only need to uncomment the HOST_ variable in order to listen in all the
net interfaces.

.. _HOST: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L4
.. _PORT: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L5

Securing the server
===================

PyBossa uses the `Flask Sessions`_ feature that signs the cookies
cryptographically for storing information. This improves the security of the
server, as the user could look at the contents of the cookie but not modify it,
unless they know the SECRET_ and SECRET_KEY_.

Therefore, **it is very important that you create a new SECRET and SECRET_KEY
keys for your server and keep them private**. Please, check the `Flask
Sessions`_ documentation for instructions about how to create good secret keys.

.. _`Flask Sessions`: http://flask.pocoo.org/docs/quickstart/#sessions

.. _SECRET: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L7
.. _SECRET_KEY : https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L8

Database username and password
==============================

PyBossa uses the SQLAlchemy_ SQL toolkit to access the DB. In the settings
file, you only need to modify the name of the user, password and database name
so it fits your needs in the field `SQLALCHEMY_DATABASE_URI`_::
    
    'postgresql://username:userpassword@localhost/databasename'
    
.. _`SQLALCHEMY_DATABSE_URI`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L10
.. _SQLAlchemy: http://www.sqlalchemy.org/

It's dangerous, so better sign this
===================================

PyBossa uses the `It's dangerous` Python library that allows you to send some
data to untrusted environments, but signing it. Basically, it uses a key that
the server only knows and uses it for signing the data. 

This library is used to send the recovery password e-mails to your PyBossa
users, sending a link with a signed key that will be verified in the server.
Thus, **it is very important you create a secure and private key for the it's
dangerous module in your configuration file**, just modify the
ITSDANGEROUSKEY_.

.. _ITSDANGEROUSKEY: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L12
.. _`It's dangerous`: http://pythonhosted.org/itsdangerous/

Modifying the Brand name
========================

You can configure your project with a different name, instead of the default
one: PyBossa. You only need to change the string BRAND_ to the name of your
organization or project.

.. _BRAND: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L15

Adding a Logo
=============

By default, PyBossa does not provide a logo for the server side, so you will
have to copy your logo into the folder: **pybossa/pybossa/static/img**. If the
logo name is, **my_brand.png** the LOGO_ variable should be updated with the
name of the file.

.. _LOGO: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L17

Terms of Use
============

You can change and modify the TERMSOFUSE_ for your server, by overriding the
provided URL that we use by default. You can also modify the license used for
the data, just change the DATAUSE_ link to the open license that you want to
use.

.. _TERMSOFUSE: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L20
.. _DATEUSE: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L21


Enabling Twitter, Facebook and Google authentication
====================================================

PyBossa supports third party authentication services like Twitter, Facebook and
Google.

Twitter
~~~~~~~

If you want to enable Twitter, you will need to create an application in
Twitter_ and copy and paste the **Consumer key and secret** into the next
variables: `TWITTER_CONSUMER_KEY`_ and `TWITTER_CONSUMER_SECRET`_ and uncomment
them.

.. _Twitter: https://dev.twitter.com/
.. _`TWITTER_CONSUMER_KEY`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L25
.. _`TWITTER_CONSUMER_SECRET`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L26

Facebook
~~~~~~~~

If you want to enable Facebook, you will need to create an application in
Facebook_ and copy and paste the **app ID/API Key and secret** into the next
variables: `FACEBOOK_APP_ID`_ and `FACEBOOK_APP_SECRET`_ and uncomment them.  

.. _Facebook: https://developers.facebook.com/apps
.. _`FACEBOOK_APP_ID`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L27
.. _`FACEBOOK_APP_SECRET`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L28


Google
~~~~~~

If you want to enable Google, you will need to create an application in
Google_ and copy and paste the **Client ID and secret** into the next
variables: `GOOGLE_CLIENT_ID`_ and `GOOGLE_CLIENT_SECRET`_ and uncomment
them.

.. _Google: https://code.google.com/apis/console/
.. _`GOOGLE_CLIENT_ID`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L29
.. _`GOOGLE_CLIENT_SECRET`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#30


Receiving e-mails with errors
=============================

If you want to receive an e-mail when an error occurs in the PyBossa server,
uncomment the ADMINS_ config variable and add a list of e-mails.

.. _ADMINS: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L34

Enabling Logging
================

PyBossa can log errors to a file_ or to a Sentry_ server. If none of the above
configurations are used, you will get the errors in the log file of the web server that you
are using (i.e. in Apache2 the errors will be in */var/log/apache2/err.log*).

.. _file: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L40
.. _Sentry: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L38

Mail Setup
==========

PyBossa needs a mail server in order to validate new accounts, send e-mails
with for recovering passwords, so it is very important you configure a server.
Please, check the section `Mail setup`_ in the config file for configuring it.

.. _`Mail setup`: https://github.com/PyBossa/pybossa/blob/master/settings_local.py.tmpl#L45

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


Tracking the server with Google Analytics
=========================================

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

Adding a Search box: Google Custom Search
=========================================

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

Adding web maps for application statistics
==========================================

PyBossa creates for each application a statistics page, where the creators of
the application and the volunteers can check the top 5 anonymous and
authenticated users, an estimation of time about when all the tasks will be
completed, etc.

One interesting feature of the statistics page is that it can generate a web
map showing the location of the anonymous volunteers that have been
participating in the application. By default the maps are disabled, because you
will need to download the GeoLiteCity DAT file database that will be use for
generating the maps.

GeoLite_ is a free geolocatication database from MaxMind that they release
under a `Creative Commons Attribution-ShareAlike 3.0 Uported License`_. You can
download the required file: GeoLite City from this page_. Once you have
downloaded the file, all you have to do is to uncompress it and place it in the
folder **/dat** of the pybossa root folder.

After copying the file, all you have to do to start creating the maps is to
restart the server.

.. _GeoLite: http://dev.maxmind.com/geoip/geolite
.. _`Creative Commons Attribution-ShareAlike 3.0 Uported License`: http://creativecommons.org/licenses/by-sa/3.0/
.. _page: http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz

Using your own Terms of Use
===========================

PyBossa has a default Terms of Service page that you can customize to fit your
institutional needs. In the case that you want to not use the default one,
please, create a **_tos.html** file in the **custom** folder (you can find it
in the templates folder.
