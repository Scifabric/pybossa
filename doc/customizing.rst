===================
Configuring PYBOSSA
===================

The PYBOSSA `settings_local.py.tmpl`_ file has all the available configuration
options for your server. This section, explains each of them and how you
should/could use them in your server.

.. _`settings_local.py.tmpl`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl

Debug mode
==========

The DEBUG_ mode is disabled by default in the configuration file, as this should
be only used when you are running the server for development purposes. You
should not enable this option, unless you need to do some debugging in the
PYBOSSA server

.. _DEBUG: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L19

.. note::
    For further details about the DEBUG mode in the PYBOSSA server, please,
    check the official documentation_.

.. _documentation: http://flask.pocoo.org/docs/quickstart/#debug-mode

Debug Toolbar
~~~~~~~~~~~~~

PYBOSSA includes a flag to enable a debug toolbar that can give your more
insights about the performance of PYBOSSA. We strongly recommend to keep the
toolbar disabled in production environments, as it will slow down considerably
all the execution of the code. However, if you are testing the server, feel
free to enable it adding the following variable to the settings file::

    ENABLE_DEBUG_TOOLBAR = True


Host and Port
=============

The HOST_ and PORT_ config variables can be used to force the server to listen
in specific addresses of your server, as well as at a given port. Usually, you
will only need to uncomment the HOST_ variable in order to listen in all the
net interfaces.

.. _HOST: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L22
.. _PORT: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L23

Securing the server
===================

PYBOSSA uses the `Flask Sessions`_ feature that signs the cookies
cryptographically for storing information. This improves the security of the
server, as the user could look at the contents of the cookie but not modify it,
unless they know the SECRET_ and SECRET_KEY_.

Therefore, **it is very important that you create a new SECRET and SECRET_KEY
keys for your server and keep them private**. Please, check the `Flask
Sessions`_ documentation for instructions about how to create good secret keys.

.. _`Flask Sessions`: http://flask.pocoo.org/docs/quickstart/#sessions
.. _SECRET: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L25
.. _SECRET_KEY : https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L26

Database username and password
==============================

PYBOSSA uses the SQLAlchemy_ SQL toolkit to access the DB. In the settings
file, you only need to modify the name of the user, password and database name
so it fits your needs in the field `SQLALCHEMY_DATABASE_URI`_::

    'postgresql://username:userpassword@localhost/databasename'

.. _`SQLALCHEMY_DATABSE_URI`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L28
.. _SQLAlchemy: http://www.sqlalchemy.org/

Load balance SQL Queries
========================

If you have a master/slave PostgreSQL setup, you can instruct PYBOSSA to use
the slave node for load balancing queries between the master and slave node.

For enabling this mode, all you have to do is adding to the settings_local.py
config file the following:

.. code-block:: python

    SQLALCHEMY_BINDS = {
        'slave': 'postgresql://user:password@server/pybossadb'
    }


It's dangerous, so better sign this
===================================

PYBOSSA uses the `It's dangerous` Python library that allows you to send some
data to untrusted environments, but signing it. Basically, it uses a key that
the server only knows and uses it for signing the data.

This library is used to send the recovery password e-mails to your PYBOSSA
users, sending a link with a signed key that will be verified in the server.
Thus, **it is very important you create a secure and private key for the it's
dangerous module in your configuration file**, just modify the
ITSDANGEROUSKEY_.

.. _ITSDANGEROUSKEY: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L35
.. _`It's dangerous`: http://pythonhosted.org/itsdangerous/

CORS configuration
==================

By default PYBOSSA has the api endpoints configured with **Access-Control-Allow-Origin: ***. However, you can change it to whatever you want via the config file. Take a look into the
official documentation for `Flask-CORS` for all the available options.

.. _`Flask-CORS`: https://flask-cors.readthedocs.io/en/latest/


Modifying the Brand name
========================

You can configure your project with a different name, instead of the default
one: PYBOSSA. You only need to change the string BRAND_ to the name of your
organization or project.

.. _BRAND: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L38

Adding a Logo
=============

By default, PYBOSSA does not provide a logo for the server side, so you will
have to copy your logo into the folder: **pybossa/pybossa/static/img**. If the
logo name is, **my_brand.png** the LOGO_ variable should be updated with the
name of the file.

.. _LOGO: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L40

Multiple languages
==================

By default PYBOSSA only speaks English, however the default theme comes with a few
translations (Spanish, French, Italian, Japanese, Greek and German). 

You can enable those translations (mostly user interface strings and actions) by doing
the following: creating a symlink to the translations folders:

.. code-block:: bash

    $ cd pybossa && ln -s themes/default/translations

This will use the default translations of PYBOSSA for your server. We recommend to use
these translations with the default theme. If you use your own theme, the best thing is
to do your own translation, (see :ref:`translating`), as you might want to name things 
differently on the templates.

You can disable/enable different languages in your config file
**settings_local.py**. For example, to remove French you can add
this configuration to the settings file:

.. code-block:: python 

    LOCALES = [('en', 'English'), ('es', u'Español'),
               ('it', 'Italiano'), ('ja', u'日本語')]


Also, you can always specify a different default locale using the following
snippet in the same settings file


.. code-block:: python 

    DEFAULT_LOCALE = 'es'


.. note::
    PYBOSSA tries to first match the user preferred language from their
    browser. This will work for anonymous users, while registered ones can
    specify the language they want using their user preferences. 


.. note::
    As an alternative way to allow anonymous users to *force* a different
    language, PYBOSSA looks for a cookie named **language** where it expects
    the key of any of the supported langes in the LOCALES list. You can use
    JavaScript to set it up.
    

Creating your own theme
=======================

PYBOSSA supports themes. By default, it provides its own theme that you can use
or if you prefer, copy it and create your own. The default theme for PYBOSSA is
available in the `repository pybossa-default-theme`_.

In order to create your theme, all you have to do is to fork the default theme
to your own account, and then start modifying it. A theme has a very simple
structure:

* info.json: this file includes some information about the author, license and
  name.
* static: this folder has all the CSS, JavaScript, images, etc. In other words,
  the static content.
* templates: this folder has the templates for PYBOSSA.

Therefore, if you want to change the look and feel (i.e. colors of the top bar)
all you have to do is to modify the styles.css file of the static folder. Or
if you prefer, create your own.

However, if you want to modify the structure, let's say you want to change the
order of the elements of the navigation bar: the first element should be the
About link, then you will have to modify the files included in the templates
folder.

As you can see, you will be able to give a full personality to your own PYBOSSA
server without problems.

.. note::
    You can specify a different amount of projects per page if you want. Change
    the default value in your settings_local.py file of APPS_PER_PAGE to the
    number that you want. By default it gives you access to 20.

.. _`repository pybossa-default-theme`: https://github.com/Scifabric/pybossa-default-theme

Using SASS and minifying JavaScript
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PYBOSSA supports SASS thanks to Flask-Assets. If you want to compile SASS or SCSS just
add to your theme static folder a new one named: sass. Then, you can request the compiled
version from the templates like this:

.. code-block:: html

    {% assets filters="libsass", output="css/gen/yourcss.min.css",
              "sass/yourcss.scss"%}
        <link rel="stylesheet" type="text/css" href="{{ ASSET_URL }}">
    {% endassets %}

The same can be done for Javascript using the filter minjs:

.. code-block:: html

    {% assets filters="jsmin", output="gen/packed.js",
              "common/jquery.js", "site/base.js", "site/widgets.js" %}
        <script type="text/javascript" src="{{ ASSET_URL }}"></script>
    {% endassets %}

Results page
=============

PYBOSSA allows you to present a results page for your server. Add a file named
_results.html to the home directory in the templates folder and you'll be able
to show results about your project from one place:

    http://server/results


Adding your Contact Information
===============================

By default, PYBOSSA provides an e-mail and a Twitter handle to contact the
PYBOSSA infrastructure. If you want, you can change it to your own e-mail and
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

.. _TERMSOFUSE: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L43
.. _DATEUSE: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L44

.. _ssnn:

Adding Help page
================

By default PYBOSSA provides a help endpoint where you can have your FAQ or similar information for your
users. However, it's empty, as each project is unique. For adding that information, create in the theme
folder: templates/help/ a file named **_index.html** and write your information in there. This will
render the information under: http://youserver.com/help/


Enabling Twitter, Facebook and Google authentication
====================================================

PYBOSSA supports third party authentication services like Twitter, Facebook and
Google.

Twitter
~~~~~~~

If you want to enable Twitter, you will need to create an application in
Twitter_ and copy and paste the **Consumer key and secret** into the next
variables: `TWITTER_CONSUMER_KEY`_ and `TWITTER_CONSUMER_SECRET`_ and uncomment
them.

.. _Twitter: https://dev.twitter.com/
.. _`TWITTER_CONSUMER_KEY`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L52
.. _`TWITTER_CONSUMER_SECRET`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L53
.. note::
    This will also enable the Twitter task importer.

Facebook
~~~~~~~~

If you want to enable Facebook, you will need to create an application in
Facebook_ and copy and paste the **app ID/API Key and secret** into the next
variables: `FACEBOOK_APP_ID`_ and `FACEBOOK_APP_SECRET`_ and uncomment them.

.. _Facebook: https://developers.facebook.com/apps
.. _`FACEBOOK_APP_ID`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L54
.. _`FACEBOOK_APP_SECRET`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L55

Google
~~~~~~

If you want to enable Google, you will need to create an application in
Google_ and copy and paste the **Client ID and secret** into the next
variables: `GOOGLE_CLIENT_ID`_ and `GOOGLE_CLIENT_SECRET`_ and uncomment
them.

.. _Google: https://code.google.com/apis/console/
.. _`GOOGLE_CLIENT_ID`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L56
.. _`GOOGLE_CLIENT_SECRET`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L57


Receiving e-mails with errors
=============================

If you want to receive an e-mail when an error occurs in the PYBOSSA server (webhooks, background jobs, etc.),
uncomment the ADMINS_ config variable and add a list of e-mails.

.. _ADMINS: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L64

Background jobs error notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can change the default behavior for receiving emails regarding failed background jobs. The two
config variables are the following:

* **FAILED_JOBS_MAILS** = 7 (days)
* **FAILED_JOBS_RETRIES** = 3 (times)

FAILED_JOBS_MAILS instructs the system to send you a reminder after 7 days, if you have not solved the issue
with the background job.

FAILED_JOBS_RETRIES instructs the system to retry the job N times. By default is 3.

Enabling Logging
================

PYBOSSA can log errors to a file_ or to a Sentry_ server. If none of the above
configurations are used, you will get the errors in the log file of the web server that you
are using (i.e. in nginx the errors will be in /var/log/nginx/error.log*).

.. _file: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L75
.. _Sentry: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L73

Mail Setup
==========

PYBOSSA needs a mail server in order to validate new accounts, send e-mails
for recovering passwords, etc. , so it is very important you configure a server.
Please, check the section `Mail setup`_ in the config file for configuring it.

.. _`Mail setup`: https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl#L80

Global Announcements for the users
==================================

Sometimes you will need to send a message to all your users while they are
browsing the server. For example, an scheduled shutdown for installing new
hardware.

PYBOSSA provides a general solution for these announcements via the
`settings_local.py.tmpl <https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl>`_
configuration file. The announcement feature allows
you to send messages to the following type of users:

 * **Authenticated users**, basically all the registered users in the server.
 * **Admin users**, all the users that are admins/root in the server.
 * **Project owners**, all the users that have created one or more
   projects in the server.

Therefore, let's say that you want to warn all your admins that a new
configuration will be deployed in your system. In this case, all you have to do
is to modify the **ANNOUNCEMENT** variable to display the message for the given
type of users:

.. code-block:: python

    ANNOUNCEMENT = {'root': 'Your secret message'}

There is an example of the **ANNOUNCEMENT** variable in the
`settings_local.py.tmpl <https://github.com/Scifabric/pybossa/blob/master/settings_local.py.tmpl>`_
file, so you can easily adapt it for your own server. Basically, the
announcement variable has a **key** and an associated **message**. The
supported keys are:

 * **admin**: for admin users
 * **user**: for all the registered users (even admins)
 * **owner**: for all registered users that have one or more projects

.. note::

    You can use a mix of messages at the same time without problems, so for
    example you can display a message for Admins and Owners at the same time.

Cache
=====

By default PYBOSSA uses Redis to cache a lot of data in order to serve it as
fast as possible. PYBOSSA comes with a default set of timeouts for different
views that you can change or modify to your own taste. All you have to do is
modify the following variables in your settings file::

    # Project cache
    APP_TIMEOUT = 15 * 60
    REGISTERED_USERS_TIMEOUT = 15 * 60
    ANON_USERS_TIMEOUT = 5 * 60 * 60
    STATS_FRONTPAGE_TIMEOUT = 12 * 60 * 60
    STATS_APP_TIMEOUT = 12 * 60 * 60
    STATS_DRAFT_TIMEOUT = 24 * 60 * 60
    N_APPS_PER_CATEGORY_TIMEOUT = 60 * 60
    BROWSE_TASKS_TIMEOUT = 3 * 60 * 60
    # Category cache
    CATEGORY_TIMEOUT = 24 * 60 * 60
    # User cache
    USER_TIMEOUT = 15 * 60
    USER_TOP_TIMEOUT = 24 * 60 * 60
    USER_TOTAL_TIMEOUT = 24 * 60 * 60

.. note::
    Every value is in seconds, so bear in mind to multiply it by 60 in order to
    have minutes in the configuration values.

Disabling the Cache
~~~~~~~~~~~~~~~~~~~

If you want to disable the cache, you only have to export the following env variable::

    PYBOSSA_REDIS_CACHE_DISABLED='1'


Rate limit for the API
======================

By default PYBOSSA limits the usage of the API with the following values::

    LIMIT = 300
    PER = 15 * 60

Those values mean that when a user sends a request to an API endpoint, a window
of 15 minutes is open, and during those 15 minutes the number of allowed
requests to the same endpoint is 300. By adding these values to your
settings_local.py file, you can adapt it to your own needs.

.. note::
    Please, be sure about what you are doing by modifying these values. This is
    the recommended configuration, so do not modify it unless you are sure.


Configuring upload method
=========================

PYBOSSA by default allows you to upload avatars for users, icons for projects, etc.
using the local file system of your server. While this is nice for small
setups, when you need to add more nodes to serve the same content, this feature
could become a problem. For this reason, PYBOSSA also supports cloud solutions
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

PYBOSSA comes with support for Rackspace CloudFiles service, allowing you to
grow horizontally the services. Suportting cloud based system is as simple as
having an account in Rackspace, and setting up the following config variables::

    UPLOAD_METHOD = 'rackspace'
    RACKSPACE_USERNAME = 'username'
    RACKSPACE_API_KEY = 'api_key'
    RACKSPACE_REGION = 'region'

Once the server is started, it will authenticate against Rackspace and since
that moment, your PYBOSSA server will save files in the cloud.

Customizing the Layout and Front Page text
==========================================

PYBOSSA allows you to override two items:

 * **Front Page Text**
 * **Footer**

If you want to override those items, you have to create a folder named
**custom** and place it in the **template** dir. Then for overriding:

 * **The Front Page Text**: create a file named  **front_page_text.html** and write there some HTML.
 * **The Footer**: create a file named  **_footer.html**, and write some HTML.


Tracking the server with Google Analytics
=========================================

PYBOSSA provides an easy way to integrate Google Analytics with your PYBOSSA
server. In order to enable it you only have to create a file with the name:
**_ga.html** in the **pybossa/template** folder with the Google Tracking code.
PYBOSSA will be including your Google Analytics tracking code in every page
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

PYBOSSA provides a simple way to search within the server pages: Google Custom
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

Adding web maps for project statistics
==========================================

PYBOSSA creates for each project a statistics page, where the creators of
the project and the volunteers can check the top 5 anonymous and
authenticated users, an estimation of time about when all the tasks will be
completed, etc.

One interesting feature of the statistics page is that it can generate a web
map showing the location of the anonymous volunteers that have been
participating in the project. By default the maps are disabled, because you
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

PYBOSSA has a default Terms of Service page that you can customize it to fit your
institutional needs. In the case that you do not want to use the default one,
please, create a **_tos.html** file in the **custom** folder. You
can re-use the template **help/_tos.html** and adapt it (it is
located in the **template/help** folder.

Using your own Cookies Policy
=============================

PYBOSSA has a default cookies policy page, but you can customize it to fit your
institutional needs. In the case that you do not want to use the default one,
please, create a **_cookies_policy.html** file in the **custom** folder. You
can re-use the template **help/_cookies_policy.html** and adapt it (it is
located in the **template/help** folder.

Using your own Privacy Policy
=============================

PYBOSSA has a blank privacy policy page. We recommend you to add one, so your
users know how you are using their data. To add it, just create a file named
**_privacy_policy.html** file in the **custom** folder.

.. _config-ckan:

Exporting data to a CKAN server
===============================

CKAN_ is a powerful data management system that makes data accessible – by providing tools to streamline publishing, sharing, finding and using data. CKAN_ is aimed at data publishers (national and regional governments, companies and organizations) wanting to make their data open and available.

PYBOSSA can export project's data to a CKAN_ server. In order to use this
feature, you will need to add the following config variables to the
settings_loca.py file:

.. code-block:: python
    # CKAN URL for API calls
    CKAN_NAME = "Demo CKAN server"
    CKAN_URL = "http://demo.ckan.org"

As CKAN_ is open source, you can install your own CKAN_ server and configure it
to host the data generated by your PYBOSSA projects quite easily, making it
the data repository for your own projects. Another alternative is to use the
`the Data hub`_ service that it is actually a free CKAN service for hosting your
data.

.. _CKAN: http://ckan.org
.. _`the Data hub`: http://datahub.io

Enforce Privacy mode
====================

Some projects need sometimes a way to protect their contributors due to the
nature of the project. In this cases, where privacy is really important,
PYBOSSA allows you to **lock** all the public pages related to the users and
statistics about the site and projects. Specifically, by enabling this mode
only administrators will be able to see the following pages:

 * http://server/stats
 * http://server/account/
 * http://server/account/user/
 * http://server/project/stats

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


Making extra key/value pairs in info field public
=================================================

By default PYBOSSA protects all the information the info field except for those
values that are public like the url of the image of the project, the container 
where that picture is stored and a few extra. While this will be more than enough
for most projects, sometimes, a server will need to expose more information publicly
via the info field for the User and Project Domain Objects.

Imagine that you want to give badges to users. You can store that information in the
User domain object, within the info field in a field named *badges*. While this will
work, the API will hide all that information except for the owner. Thus, it will be impossible
to show user's badges to anonymous people.

With projects it could be the same. You want to highlight some info to anyone, but hide everything else.

As PYBOSSA hides everything by default, you can always turn on which other fields from the
info field can be shown to anonymous users, making them public. 

.. note::

    WARNING: be very careful. This is your responsibility, and it's not enabled by default. If you
    expose your own private data via this field, it's your own responsibility as this is not enabled
    by default in PYBOSSA.

If you want to make some key/values public, all you have to do is add to the settings_local.py file
the following config variables::

    PROJECT_INFO_PUBLIC_FIELDS = ['key1', 'key2']
    USER_INFO_PUBLIC_FIELDS = ['badges', 'key2', ...]

Add as many as you want, need. But please, be careful about which information you disclose.

Adding your own templates
=========================

PYBOSSA supports different types of templates that you can offer for every
project. By default, PYBOSSA comes with the following templates:

 * **Basic**: the most basic template. It only has the basic structure to
   develop your project.
 * **Image**: this template is for image pattern recognition.
 * **Sound**: similar to the image template, but for sound clips hosted in
   SoundCloud.
 * **Video**: similar to the imaage template, but for video clips hostes in
   Vimeo.
 * **Map**: this template is for geocoding prorjects.
 * **PDF**: this template is for transcribing documents.

If you want to add your own template, or remove one, just create in the
settings_local.py file a variable named **PRESENTERS** and add remove the ones
you want::

    PRESENTERS = ["basic", "image", "sound", "video", "map", "pdf", "yourtemplate"]

**Yourtemplate** should be a template that you have to save in the theme
folder: **/templates/projects/snippets/** with the same name. Check the
other templates to use them as a base layer for your template.

After adding the template, the server will start offering this new template to
your users.

In addition to the project templates themselves, you can add some test tasks for
those projects so that the users can import them to their projects and start
"playing" with them, or taking their format as a starting point to create their
own. These tasks can be imported from Google Docs spreadsheets, and you can add
them, remove them, or modify the URLs of the spreadsheets changing the value of
the variable **TEMPLATE_TASKS** in settings_local.py::

TEMPLATE_TASKS = {
    'image': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc&usp=sharing",
    'video': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdGZ2UGhxSTJjQl9YNVhfUVhGRUdoRWc&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE&usp=sharing"}

Setting an expiration time for project passwords
================================================

PYBOSSA allows the owner of a project to set a password so that only people
(both anonymous or authenticated) that know it can contribute. By entering this
password, the user will have access to the project for a time specified by::

    PASSWD_COOKIE_TIMEOUT = 60 * 30

Which defaults to 30 minutes.

Validation of new user accounts
===============================

Whenever a new user wants to sign up, PYBOSSA allows you to add some extra
security to the process by making the users have to validate a real email account.

However, if you don't need this feature, it can be disabled (as it is by default)
with this configuration parameter::

    ACCOUNT_CONFIRMATION_DISABLED = True

Sending weekly email stats to project owners
============================================

Project owners that have the pro flag set to True can receive every week an
update with the latest statistics about their projects in their email box.

By default this email is sent every Sunday. You can modify it in the settings
file by changing it to another day:

WEEKLY_UPDATE_STATS = 'Tuesday'

Newsletters with Mailchimp
==========================

PYBOSSA can show a subscription page to users when they create an account. By
default is disabled, but if you want to enable it the system will show the page
to registered users only once, to check if they want to be subscribed or not.

In order to support newsletters, you'll have to create an account in Mailchimp
and get an API_KEY as well as a LIST_ID to add the users. Once you've those two
items you can enable the newsletter subscription as simple as this, add to your
settings_local.py file the following values::

    MAILCHIMP_API_KEY = "your-key"
    MAILCHIMP_LIST_ID = "your-list-id"

Restart the server, and you will be done. Now in your Mailchimp account you
will be able to create campaigns, and communicate with your registered and
interested users.

Enabling the Flickr Task importer
=================================

PYBOSSA has several different types of built-in importers. Users can use them to
import tasks for their projects directly from the Web interface. However, using
the Flickr one requires an API key and shared secret from Flickr in order to
communicate with the service.

Once you have an API key, you'll have to add it to your settings_local.py file::

    FLICKR_API_KEY = "your-key"
    FLICKR_SHARED_SECRET = "your-secret"

For more information on how to get a Flickr API key and shared secret, please
refer to `here <https://www.flickr.com/services/api/>`_.

Enabling the Dropbox Task importer
==================================

PYBOSSA also offers the Dropbox importer, which allows to import directly all
kind of files from a Dropbox account. In order to use it, you'll need to
register your PYBOSSA server as a Dropbox app, as explained
`here <https://www.dropbox.com/developers/dropins/chooser/js#setup>`_.

Don't worry about the Javascript snippet part, we've already handled that for you.
Instead, get the App key you will be given and add it to your settings_local.py::

    DROPBOX_APP_KEY = 'your-key'

Enabling the Twitter Task importer
==================================

If you already have enabled the Twitter authentication, then the Twitter task
importer will be enabled too. Otherwise, you will need to create an application
in Twitter_ and copy and paste the **Consumer key and secret** into the next
variables: `TWITTER_CONSUMER_KEY`_ and `TWITTER_CONSUMER_SECRET`_ and uncomment
them.

.. _Twitter: https://dev.twitter.com/
.. note::
    This will also enable PYBOSSA's Twitter login.

Enabling the Youtube Task importer
==================================

The Youtube task importer needs a Youtube server key which you need to create in the `Google API Console <https://console.developers.google.com/>`_ in YouTube Data API.

Once you have an API key, you'll have to add it to your settings_local.py file::

    YOUTUBE_API_SERVER_KEY = "your-key"

For more information on how to get a Youtube server key, please
refer to `here <https://developers.google.com/youtube/registering_an_application#Create_API_Keys>`_.

Enabling Server Sent Events
===========================

Since PYBOSSA v1.1.0, PYBOSSA supports Server Sent Events (SSE) in some views. This feature
is really powerfull, however it brings some issues with it: it need to run PYBOSSA in
asynchronous mode.

As this is not a necessity, by default PYBOSSA has this feature disabled. PYBOSSA uses
SSE to notify users about specific actions (i.e. the result of a webhook in real time).

If you want to enable it, you will have to add to your settings_local.py::

    SSE = True

Also, you will need to configure uwsgi and nginx to support SSE events. This is not 
trivial, as there are several different scenarios, libraries and options, so instead of
recommending one solution, we invite you to read the `uwsgi documentation about it <http://uwsgi-docs.readthedocs.org/en/latest/Async.html>`_, so you can take a decission based on your
own infrastructure and preferences.

Latest news from PYBOSSA
========================

Since version v1.2.1 PYBOSSA gets the latest news of its new releases, as well
as anything related to what it's produced by SciFabric regarding the crowdsourcing
world. You can add more items if you want, by just adding to your settings_local.py
file new ATOM URLs::

    NEWS_URL = ['http:/http:///atomurl1', 'http://atomurl2', ...]

Enabling pro user features
==========================

Since version v1.2.2 PYBOSSA allows making available to all the users certain
features that were before reserved to pro users.

Just locate them in the settings_local.py file. By default, they look like::

    PRO_FEATURES = {
        'auditlog':              True,
        'webhooks':              True,
        'updated_exports':       True,
        'notify_blog_updates':   True,
        'project_weekly_report': True,
        'autoimporter':          True,
        'better_stats':          True
    }

By choosing "True" on each of them, you are making that specific feature available
only to pro users. On the other hand, selecting "False" makes them available
to regular users as well.

Strict Slashes
==============

By default PYBOSSA distinguish between two types of URLs for its endpoints: with and without a traling slash. In other words, if an endpoint is not declared within the code as accepting both options, accessing the same endpoint with a trailing slash will return a 404.

For example, the about endpoint::

    GET /about

Will return the page, but with the default configuration it will return a 404 if you add a trailing slash to it::

    GET /about/

To disable this behavior, just use the STRICT_SLASHES option and set it to False. That option willensure that both endpoints works with and without the trailing slash.

.. _disqus:

Disqus Single Sign On (SSO)
===========================

PYBOSSA supports Disqus SSO, however it is disabled by default. You need to register a Disqus application (see their `documentation`_) and then update your settings_local.py file with the following two keys::

    DISQUS_SECRET_KEY
    DISQUS_PUBLIC_KEY

Then, this will enable you to use a new Jinja2 filter for authenticating PYBOSSA users directly in their Disqus server. The filter is *disqus_sso*. You can use it like this::

    {% if current_user.is_authenticated() %}
    {{ current_user | disqus_sso | safe }}
    {% else %}
    {{ None | disqus_sso | safe }}
    {% endif %}

Also, if you are building a Single Page Application, you can use our API endpoint: *api/disqus/sso* to get the credentials and authenticate the users within your javascript. Check the endpoint information :ref:`disqus-api`.

.. _`documentation`: https://help.disqus.com/customer/portal/articles/236206

Background jobs timeout
=======================

By default PYBOSSA timeout for every job is 10 minutes. In principle it should be fine,
but each project and server is unique, so if you start seeing to many jobs failing because
the job timed out, then, increase the value using this config variables::

    MINUTE = 60
    TIMEOUT = 20 * 60

Web Push notifications
======================

.. note::

    You need to have HTTPS enabled for your site, otherwise you will need to use a subdomain from
    onesignal.com in order to support this feature. If you cannot use HTTPS we recommend to not enable
    it.

PYBOSSA can send web push notifications to Google Chrome, Mozilla Firefox and Safari browsers. 

For supporting this feature, PYBOSSA uses the Onesignal.com service. You will need an account and create
an app for your PYBOSSA server. Then follow their documentation to download the WebPush SDK and configure
your PYBOSSA theme.

For more info regarding Onesignal, check their `documentation. <https://documentation.onesignal.com/docs/web-push-setup>`_

.. note::

    You can host the SDK files in the static folder of your theme. However you will need to modify your
    web server (Apache or Nginx) to serve those files as from the root of your server. If this is not
    done properly, it will not work.

After you have created the app in Onesignal get the API KEY and APP ID. Then copy them and put it in your
settings_local.py file::

    ONESIGNAL_APP_ID = 'app-id'
    ONESIGNAL_API_KEY = 'app-key'

Restart the server, and add one background worker for the *webpush* queue. This queue will handle the 
creation of the apps, as well as sending the push notifications.

Then you will need to update your PYBOSSA theme in order to allow your users to subscribe. As this could
vary a lot from one project to another, we do not provide a template but some guidelines:

 * Use the JS SDK to subscribe a user to a given project using the *tags* option of Onesignal. 
 * PYBOSSA sends notifications using those tags thanks to the *filters* option that allows us to
   segment traffic. PYBOSSA is especting the project.id as the tag key for segmenting.
 * The JS SDK allows you to subscribe/unsubscribe a user to a give project (not only the whole server) with
   special methods for adding tags and deleting them. This works independently if the user is authenticated
   or not.

For more info regarding Onesignal JS SDK, check their `documentation. <https://documentation.onesignal.com/docs/web-push-sdk>`_
