.. image:: https://travis-ci.org/PyBossa/pybossa.png
   :target: https://travis-ci.org/#!/PyBossa/pybossa

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

PyBossa powers `CrowdCrafting.org <http://crowdcrafting.org/>`_ 
and `ForestWatchers.net <http://forestwatchers.net>`_

Installing and Upgrading
========================

**Important: if you are updating a server, please, be sure to check the
Database Migration scripts, as new changes could introduce new tables,
columns, etc, in the DB model. See the `Migration Section`_ from the
documentation**

.. _`Migration Section`: http://docs.pybossa.com/en/latest/install.html#migrating-the-database-table-structure

See `installation instructions <http://docs.pybossa.com/en/latest/install.html>`_.

Running Tests
=============

Set SQLALCHEMY_DATABASE_TEST_URI e.g.::

  SQLALCHEMY_DATABASE_URI = 'postgres://pybossa:pass@localhost/pybossa'

Then run the tests (requires nose)::

  nosetests -v test/


Useful Links
============

* `Documentation <http://docs.pybossa.com/>`_
* `Mailing List <http://lists.okfn.org/mailman/listinfo/open-science-dev>`_


Authors
=======

* Daniel Lombraña González - Citizen Cyberscience Centre
* Rufus Pollock - Open Knowledge Foundation
* Chris Powell - EPICollect
* David Anderson - BOINC / Berkeley (via BOSSA)

* Twitter Bootstrap Icons by Glyphicons http://http://glyphicons.com/
* FontAwesome fonts by http://fortawesome.github.com/Font-Awesome/
* GeoLite data by MaxMind http://www.maxmind.com
