==================================
Welcome to PyBossa's documentation
==================================

PyBossa is an open source platform for crowd-sourcing online (volunteer)
assistance to perform tasks that require human cognition, knowledge or
intelligence (e.g. image classification, transcription, information location
etc). 

PyBossa was inspired by the BOSSA_ crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks project
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

The documentation is organized as follows:

.. toctree::
   :maxdepth: 1

   build_with_pybossa
   admin
   installing_pybossa
   vagrant_pybossa
   faq

.. _BOSSA: http://bossa.berkeley.edu/

====
News
====

The latest version of PyBossa is 0.2.0 and has several changes regarding how
the web service caches domain objects. If you are running a previous version,
please, be sure to read how to install Redis_ software and configure two
instances of it:

* the DB and 
* the Sentinel_ mode.

.. _Redis: http://redis.io/
.. _Sentinel: http://redis.io/topics/sentinel
  
For more information, check :ref:`pybossa-cache`.

Changelog
~~~~~~~~~

* v0.2.3_
* [v0.2.1] New Rate Limiting for all the API endpoints
* [v0.2.0] New CACHE system using Redis Master-Slave infrastructure

.. _v0.2.3: changelog/v0.2.3.html


============
Useful Links
============

* Mailing list: http://lists.okfn.org/mailman/listinfo/okfn-labs
* Source code: https://github.com/PyBossa/pybossa
* Template apps: https://github.com/PyBossa

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
