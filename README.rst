BOSSA in Python

# Install

Install the code and requirements (you may wish to create a virtualenv first)::

  # get the source
  git clone https://github.com/okfn/pybossa
  cd pybossa
  # [optional] create virtualenv first
  # virtualenv ~/{my-virtualenv}
  pip install -e .

[Optional] Add to or override the default settings by copying the provided
template (in pybossa/default_settings.py)::

  cp settings_local.py.tmpl settings_local.py

Alternatively, if you want your config elsewhere or with different name::

  cp settings_local.py.tmpl {/my/config/file/somewhere}
  export PYBOSSA_SETTINGS={/my/config/file/somewhere}

Run the web server::

  python pybossa/web.py

