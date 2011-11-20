BOSSA in Python

Install
=======

Pre-requisites:

  * Python >= 2.6, <3.0
  * MySQL database
  * Python MySQL bindings (e.g. on ubuntu python-mysqldb)

Install the code and requirements (you may wish to create a virtualenv first)::

  # get the source
  git clone https://github.com/okfn/pybossa
  cd pybossa
  # [optional] create virtualenv first
  # virtualenv ~/{my-virtualenv}
  pip install -e .

Create a settings file and enter your SQLAlchemy DB URI (you can also override
default settings as needed)::

  cp settings_local.py.tmpl settings_local.py
  # now edit ...
  vim settings_local.py

Alternatively, if you want your config elsewhere or with different name::

  cp settings_local.py.tmpl {/my/config/file/somewhere}
  export PYBOSSA_SETTINGS={/my/config/file/somewhere}

Run the web server::

  python pybossa/web.py

