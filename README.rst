PyBossa is an open source platform for crowd-sourcing online (volunteer)
assistance to perform tasks that require human cognition, knowledge or
intelligence (e.g. image classification, transcription, information location
etc). 

PyBossa was inspired by the BOSSA_ crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks application
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

.. _BOSSA: http://bossa.berkeley.edu/


See it in Action
================

PyBossa powers http://pybossa.com/ - check it out!


Install
=======

See doc/install.rst or http://pybossa.readthedocs.org/en/latest/install.html

Deploying
=========

ep.io
-----

For background see:
http://notebook.okfn.org/2011/12/10/deploying-a-flask-app-on-ep-io/

0. Set up as per ep.io instructions https://www.ep.io/docs/quickstart/flask/

1. Create epio.ini file containing::

    [wsgi]
    entrypoint = pybossa.web:app
    requirements = requirements.txt

    [services]
    postgres = true

    [env]
    PYBOSSA_SETTINGS = ../settings_epio.py

2. Create .epio-app file containing single line::

    pybossa

3. Create .epioignore file e.g.::

    *.egg-info
    .*.swp
    *.pyc
    settings_local.py
    doc/
 
4. Run the upload command::

    epio upload


Useful Links
============

* Documentation: http://pybossa.readthedocs.org/
* Mailing List http://lists.okfn.org/mailman/listinfo/open-science-dev


Authors
=======

* Daniel Lombraña González - Citizen Cyberscience Centre
* Rufus Pollock - Open Knowledge Foundation
* Chris Powell - EPICollect
* David Anderson - BOINC / Berkeley (via BOSSA)

* Twitter Bootstrap Icons by Glyphicons http://http://glyphicons.com/
* FontAwesome fonts by http://fortawesome.github.com/Font-Awesome/


