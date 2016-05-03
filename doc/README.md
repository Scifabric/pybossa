PyBossa Sphinx Docs Creation
============================

To create and preview docs (once):

1. Activate virtualenv from PyBossa: `source ../env/bin/activate`.
2. Build docs with `make html`
3. Open with your browser of choice `./_build/html/index.html` or open a local webserver in `./_build/html/`

To create and preview docs on every file change:

1. Activate virtualenv from PyBossa: `source ../env/bin/activate`.
2. Install sphinx-autobuild: `pip install sphinx-autobuild`
3. Run `make livehtml`
4. Open Browser on [http://127.0.0.1:8000](http://127.0.0.1:8000)