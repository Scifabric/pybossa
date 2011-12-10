PyBossa is an open source platform for crowd-sourcing online (volunteer)
assistance to perform tasks that require human cognition, knowledge or
intelligence (e.g. image classification, transcription, information location
etc). 

PyBossa was inspired by the BOSSA_ crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks application
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

.. _BOSSA: http://bossa.berkeley.edu/

Install
=======

Pre-requisites:

  * Python >= 2.6, <3.0
  * MySQL database plus Python MySQL bindings (e.g. on ubuntu python-mysqldb)
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

