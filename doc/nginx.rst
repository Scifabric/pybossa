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

The PyBossa virtual host file (**contrib/nginx/pybossa**) has the
following directives::

    location / { try_files $uri @pybossa; }

    location @pybossa {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/pybossa.sock;
    }

    location  /static {

                # change that to your pybossa static directory
                alias /home/pybossa/pybossa/pybossa/themes/default/static;

                autoindex on;
                expires max;
            }

.. note:

    This guide is assumming that you are going to serve the application from a home
    folder, not the standard */var/www* DocumentRoot of Apache.

You can specify a user and group from your machine with lower privileges in
order to improve the security of the site. You can also use the www-data user
and group name.

Once you have adapted the PATH in the alias in that file, copy it into the folder::

    sudo cp contrib/nginx/pybossa /etc/nginx/sites-available/.

please delete the default config in sites-enabled (do not worry there is a backup)::

    sudo rm /etc/nginx/sites-enabled/default

Enable the PyBossa site::

    sudo ln -s /etc/nginx/sites-available/pybossa /etc/nginx/sites-enabled/pybossa

And restart the server::

 $ sudo service nginx restart

Creating the pybossa.ini file for uwsgi
---------------------------------------

You only have to copy the **pybossa.ini.template** file to
pybossa.ini and adapt the paths to match your configuration!

The content of this file is the following::

  [uwsgi]
  socket = /tmp/pybossa.sock
  chmod-socket = 666
  chdir = /home/pybossa/pybossa
  pythonpath = ..
  virtualenv = /home/pybossa/pybossa/env
  module = run:app
  cpu-affinity = 1
  processes = 2
  threads = 2
  listen = 2048
  stats = /tmp/pybossa-stats.sock
  buffer-size = 65535

Restart the web server and you should be able to see your PyBossa web
application up and running in http://example.com
