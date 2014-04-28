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

Creating your own theme
=======================

PyBossa supports themes. By default, it provides its own theme that you can use
or if you prefer, copy it and create your own. The default theme for PyBossa is
available in the `repository pybossa-default-theme`_.

In order to create your theme, all you have to do is to fork the default theme
to your own account, and then start modifying it. A theme has a very simple
structure:

* info.json: this file includes some information about the author, license and
  name.
* static: this folder has all the CSS, JavaScript, images, etc. In other words,
  the static content.
* templates: this folder has the templates for PyBossa.

Therefore, if you want to change the look and feel (i.e. colors of the top bar)
all you have to do is to modify the styles.css file of the static folder. Or
if you prefer, create your own.

However, if you want to modify the structure, let's say you want to change the
order of the elements of the navigation bar: the first element should be the
About link, then you will have to modify the files included in the templates
folder.

As you can see, you will be able to give a full personality to your own PyBossa
server without problems.

.. note::
    You can specify a different amount of apps per page if you want. Change the
    default value in your settings_local.py file of APPS_PER_PAGE to the number
    that you want. By default it gives you access to 20.

.. _`repository pybossa-default-theme`: https://github.com/PyBossa/pybossa-default-theme

Adding your Contact Information
===============================

By default, PyBossa provides an e-mail and a Twitter handle to contact the
PyBossa infrastructure. If you want, you can change it to your own e-mail and
Twitter account. You can do it, modifying the following variables in the
**settings_local.py** file:

* **CONTACT_EMAIL** = 'your@email.com'
* **CONTACT_TWITTER** = 'yourtwitterhandle'

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

Disabling the Cache
===================

PyBossa comes with its own Cache system (based on Redis) that it is
enabled by default. If you want to disable the cache, you
only have to export the following env variable::

    PYBOSSA_REDIS_CACHE_DISABLED='1'


Configuring upload method
=========================

PyBossa by default allows you to upload avatars for users, icons for apps, etc.
using the local file system of your server. While this is nice for small
setups, when you need to add more nodes to serve the same content, this feature
could become a problem. For this reason, PyBossa also supports cloud solutions
to save the files and serve them from there properly.

Local Uploader
--------------

The local uploader is configured by default. We recommend to have a separate
folder for the assets, outside the pybossa folder. In any case, for enabling
this method use the following the config settings::

    UPLOAD_METHOD = 'local'
    UPLOAD_FOLDER = '/absolute/path/to/your/folder/to/store/assets/'

Rackspace Cloud Files
---------------------

PyBossa comes with support for Rackspace CloudFiles service, allowing you to
grow horizontally the services. Suportting cloud based system is as simple as
having an account in Rackspace, and setting up the following config variables::

    UPLOAD_METHOD = 'rackspace'
    RACKSPACE_USERNAME = 'username'
    RACKSPACE_API_KEY = 'api_key'
    RACKSPACE_REGION = 'region'

Once the server is started, it will authenticate against Rackspace and since
that moment, your PyBossa server will save files in the cloud.

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

PyBossa has a default Terms of Service page that you can customize it to fit your
institutional needs. In the case that you do not want to use the default one,
please, create a **_tos.html** file in the **custom** folder. You
can re-use the template **help/_tos.html** and adapt it (it is
located in the **template/help** folder.

Using your own Cookies Policy
=============================

PyBossa has a default cookies policy page, but you can customize it to fit your
institutional needs. In the case that you do not want to use the default one,
please, create a **_cookies_policy.html** file in the **custom** folder. You
can re-use the template **help/_cookies_policy.html** and adapt it (it is
located in the **template/help** folder.

.. _config-ckan:

Exporting data to a CKAN server
===============================

CKAN_ is a powerful data management system that makes data accessible – by providing tools to streamline publishing, sharing, finding and using data. CKAN_ is aimed at data publishers (national and regional governments, companies and organizations) wanting to make their data open and available.

PyBossa can export application's data to a CKAN_ server. In order to use this
feature, you will need to add the following config variables to the
settings_loca.py file:

.. code-block:: python
    # CKAN URL for API calls
    CKAN_NAME = "Demo CKAN server"
    CKAN_URL = "http://demo.ckan.org"

As CKAN_ is open source, you can install your own CKAN_ server and configure it
to host the data generated by your PyBossa applications quite easily, making it
the data repository for your own projects. Another alternative is to use the
`the Data hub`_ service that it is actually a free CKAN service for hosting your
data.

.. _CKAN: http://ckan.org
.. _`the Data hub`: http://datahub.io

Enforce Privacy mode
====================

Some projects need sometimes a way to protect their contributors due to the
nature of the project. In this cases, where privacy is really important,
PyBossa allows you to **lock** all the public pages related to the users and
statistics about the site and applications. Specifically, by enabling this mode
only administrators will be able to see the following pages:

 * http://server/stats
 * http://server/account/
 * http://server/account/user/
 * http://server/app/stats

Anonymous and authenticated will see a warning message like this:

.. image:: http://i.imgur.com/a1aqSCC.png

Additionally, the footer and front page top users will be removed with links to
all these pages. If your project needs this type of protection you can enable
it by changing the following config variable in your **settings_local.py** file from:

.. code-block:: python
    
    ENFORCE_PRIVACY = False

To:

.. code-block:: python
    
    ENFORCE_PRIVACY = True


.. note::
    This feature is disabled by default.
