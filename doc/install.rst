==================
Installing PyBossa
==================

PyBossa is a python web application built using the Flask micro-framework.

Pre-requisites:

  * Python >= 2.6, <3.0
  * A database plus Python bindings (any database compatible with SQLAlchemy is fine but current devs tend to use Postgresql)
  * pip for installing python packages (e.g. on ubuntu python-pip)

Install the code and requirements (you may wish to create a virtualenv first)::

  # get the source
  git clone https://github.com/citizen-cyberscience-centre/pybossa
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

Setup the database::

  python cli.py db_create

Run the web server::

  python pybossa/web.py


