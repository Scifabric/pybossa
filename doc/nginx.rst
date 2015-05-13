=================================================
Deploying PyBossa with nginx web server and uwsgi
=================================================

PyBossa is a python web application built using the Flask micro-framework.

To run PyBossa you need a **pybossa.wsgi** file. This file contains the code
*mod_wsgi* is executing on startup to get the application object. The object
named *application* in that file is then used as an application.

Pre-requisites:

  * nginx
  * uwsgi

Installing nginx and uwsgi
--------------------------

You have to install nginx and uwsgi in your server machine. In
a Debian/Ubuntu machine you can install them running the following commands::

   sudo apt-get install nginx

in the (virtualenv-)installation directory of pybossa you need to install uwsgi::

   pip install -U uwsgi

Configuring nginx and uwsgi for PyBossa
---------------------------------------

We assume you only want to run PyBossa on your nginx webserver. If you want to
run also other services on the same server you need to modify the nginx config files!

You have to copy and adapt the following files from your local PyBossa
installation:

 * contrib/nginx/pybossa
 * contrib/pybossa.ini

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
