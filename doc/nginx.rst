======================================
Deploying PyBossa with nginx and uwsgi
======================================

PyBossa is a python web application built using the Flask micro-framework.

This guide describes how to make PyBossa run as a service or daemon permanently
in the background. This is useful if you want to run a production ready single
PyBossa web server. If you only want to test PyBossa please follow only :doc:`install`.

Pre-requisites:

  * nginx
  * uwsgi
  * supervisord
  * Redis and sentinel as service (with supervisord)
  * RQ-Scheduler and RQ-Worker as service (with supervisord)
  * PyBossa as service (with supervisord)

First steps
-----------

If you have not done already: Please create a new user account, e.g. pybossa
(a non root at best) which will run the PyBossa instance.
You then have to follow the instructions from :doc:`install` first to get
a runnable PyBossa. After you've done that please continue with this guide.

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

    sudo service nginx restart

Creating the pybossa.ini file for uwsgi
---------------------------------------

You have to copy the **pybossa.ini.template** file to
pybossa.ini in your PyBossa installation and adapt the paths to match your configuration!

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
  stats = /tmp/pybossa-stats.sock
  buffer-size = 65535

Install supervisord
-------------------

Supervisord is used to let PyBossa and its RQ system run as Daemon in the background.
It shares some of the same goals of programs like launchd, daemontools, and runit.

Install it::

  sudo apt-get install supervisor

Configure Redis and sentinel as service with supervisord
--------------------------------------------------------

First stop redis service and all running redis instances with::

  sudo service redis-server stop
  killall redis-server

We want to run redis and sentinel with supervisord because supervisord is more
reliable when redis crashes (which can happen when you have too less memory).
So we disable redis-server daemon service with::

  sudo rm /etc/init.d/redis-server

Go to your pybossa installation directory and copy following files::

  sudo cp contrib/supervisor/redis-server.conf /etc/supervisor/conf.d/
  sudo cp contrib/supervisor/redis-sentinel.conf /etc/supervisor/conf.d/
  sudo cp contrib/redis-supervisor/redis.conf /etc/redis/
  sudo cp contrib/redis-supervisor/sentinel.conf /etc/redis/
  sudo chown redis:redis /etc/redis/redis.conf
  sudo chown redis:redis /etc/redis/sentinel.conf

Now we restart supervisord (please do a full stop and start as described)::

  sudo service supervisor stop
  sudo service supervisor start

To verify install you can list all redis processes and you should see a
redis-server at port 6379 and redis-sentinel at port 26379::

  ps aux | grep redis

This two services will no run whenever the server is running (even after reboot).

Configure RQ-Scheduler and -Worker to run with supervisord
----------------------------------------------------------

You need to adjust the paths and user account in this two config files
according to your installation!
Then copy them to supervisor (do not forget to edit them)::

  sudo cp contrib/supervisor/rq-scheduler.conf.template /etc/supervisor/conf.d/rq-scheduler.conf
  sudo cp contrib/supervisor/rq-worker.conf.template /etc/supervisor/conf.d/rq-worker.conf

Restart supervisor fully::

  sudo service supervisor stop
  sudo service supervisor start

Verify service running. You should see a rqworker and rqscheduler instance in
console::

  ps aux | grep rq

Setup PyBossa itself
--------------------

This steps are recommended to do when you run PyBossa in nginx. Open your **settings_local.py** in your PyBossa
installation and uncomment or delete the two lines with **HOST** and **PORT**, e.g.::

  # HOST = '0.0.0.0'
  # PORT = 12000

After that specify the full server URL where your PyBossa is reachable, e.g.::

  SERVER_NAME = mypybossa.com
  PORT = 80

Let PyBossa run as service
--------------------------

Finally we need to let pybossa run as service. Adjust again the paths and
user name in this file and copy it to supervisor config directory::

  sudo cp contrib/supervisor/pybossa.conf.template /etc/supervisor/conf.d/pybossa.conf

Edit now the file and adjust paths & user name.

Restart supervisor fully::

  sudo service supervisor stop
  sudo service supervisor start

You should now have a running PyBossa production ready webserver on your nginx.
Open your browser and check your configured domain http://example.com.

Congratulations! :)


How to update PyBossa service
-----------------------------

Upgrading and updating PyBossa as service works the same as for a standalone
version. Please follow instructions on :doc:`install`.
However a few extra steps are required after you updated.

You need to restart all supervisor controlled services after updating::

  sudo supervisorctl restart rq-scheduler
  sudo supervisorctl restart rq-worker
  sudo supervisorctl restart pybossa

Logs of PyBossa services
------------------------

You can find logs of all PyBossa services in this directory::

  cd /var/log/supervisor


Last words about Security and Scaling
--------------------------------------

This guide does not cover how to secure your PyBossa installation.
As every web server you have to make it secure
(like e.g. strong passwords, automatic Ubuntu security updates, firewall,
access restrictions).
Please use guides on the Internet to do so.

PyBossa can also be scaled horizontally to run with redundant servers and with zero
downtime over many redis, db and web servers with load balancers in between.

If you need a secure and/or scalable PyBossa installation please contact us.
We will be glad to help you and we can even do all the hosting, customization,
administration and installation for you when you want for a small fee.

Contact address:

info@pybossa.com
