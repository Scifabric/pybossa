======================================================
Deploying PyBossa with Apache2 web server and mod_wsgi
======================================================

PyBossa is a python web application built using the Flask micro-framework.

To run PyBossa you need a **pybossa.wsgi** file. This file contains the code
*mod_wsgi* is executing on startup to get the application object. The object
named *application* in that file is then used as an application.

Pre-requisites:

  * Apache2
  * mod_wsgi

Installing Apache2 and mod_wsgi
-------------------------------

You have to install Apache2 and mod_wsgi in your server machine. In
a Debian/Ubuntu machine you can install them running the following commands::

 $ sudo apt-get install apache2
 $ sudo apt-get install libapache2-mod-wsgi

After installing the software, you have to enable the *mod_wsgi* library and
restart the web server::

 $ sudo a2enmod wsgi
 $ sudo /etc/init.d/apache2 restart

Creating a Virtual Host for running PyBossa
-------------------------------------------

Now you have to copy and adapt the following files from your local PyBossa
installation:

 * contrib/apache2/pybossa-site
 * contrib/pybossa.wsgi

The PyBossa virtual host file (**contrib/apache2/pybossa-site**) has the
following directives::

    <VirtualHost *:80>
        ServerName example.com
    
        DocumentRoot /home/user/pybossa
        WSGIDaemonProcess pybossa user=user1 group=group1 threads=5
        WSGIScriptAlias / /home/user/pybossa/contrib/pybossa.wsgi
    
        <Directory /home/user/pybossa>
            WSGIProcessGroup pybossa
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
    </VirtualHost>

.. note:

    This guide is assumming that you are going to serve the application from a home
    folder, not the standard */var/www* DocumentRoot of Apache.

You can specify a user and group from your machine with lower privileges in
order to improve the security of the site. You can also use the www-data user
and group name.

Once you have adapted the PATH in that file, copy it into the folder::

 /etc/apache2/sites-available

Enable the site::

    sudo a2ensite pybossa-site

And restart the server::

 $ sudo /etc/init.d/apache2 restart

Creating the pybossa.wsgi file
------------------------------

Finally, you only have to copy the **pybossa.wsgi.template** file to
pybossa.wsgie and adapt the paths to match your configuration.

The content of this file is the following::

  # Check the official documentation http://flask.pocoo.org/docs/deploying/mod_wsgi/
  # Activate the virtual env (we assume that virtualenv is in the env folder)
  activate_this = '/home/user/pybossa/env/bin/activate_this.py'
  execfile(activate_this, dict(__file__=activate_this))
  # Import sys to add the path of PyBossa
  import sys
  sys.path.insert(0,'/home/user/pybossa')
  # Run the web-app
  from pybossa.web import app as application


Restart the web server and you should be able to see your PyBossa web
application up and running in http://example.com

Configuring a maintenance mode
------------------------------

The service will be updated from time to time, so in order to show the
maintenance of your site, you can use the **pybossa-maintenance** template
in the *contrib* folder to enable this mode.

The solution is really simple, we set up a new virtual host that will redirect
all the requests to the maintenance web page. The steps to use this solution
are the following:

 * Copy pybossa-maintenance to Apache2 **sites-available** folder
 * Enable the Headers mod for Apache: a2enmod headers
 * Restart Apache2

Once you have set up the server, if you want to enable the **maintenance mode**
all you have to do is run the following commands::

  # a2dissite pybossa-site
  # a2ensite pybossa-maintenance
  # service apache2 reload

As you can see, we first disable the current configuration for pybossa, then we 
enable the redirections, and finally we force the server to re-read the
configuration. 

.. note::
    Be sure to create a maintenance.html file in the **DocumentRoot** of your
    Apache server, otherwise it will not work.

To going into production mode again, just run the following commands::

 # a2dissite pybossa-maintenance
 # a2ensite pybossa-site
 # service apache2 reload

You can copy and paste the following BASH script for starting/stopping
PyBossa with just one command::

    
    #!/bin/bash
    
    if [ $1 == "stop" ]
    then
            a2dissite pybossa-site
            a2ensite maintenance
            service apache2 reload
    fi
    
    if [ $1 == "start" ]
    then
            a2dissite maintenance
            a2ensite pybossa-site
            service apache2 reload
    fi

Therefore, you can run::

    $ sudo script-name stop

To put PyBossa in maintenance mode, and::

    $ sudo script-name start

To start again PyBossa. You can integrate this into your deployment system without too many problems.
