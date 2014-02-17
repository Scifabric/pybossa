[![Travis CI](https://travis-ci.org/PyBossa/pybossa.png?branch=master)](https://travis-ci.org/#!/PyBossa/pybossa)  [![Coverage Status](https://coveralls.io/repos/PyBossa/pybossa/badge.png?branch=master)](https://coveralls.io/r/PyBossa/pybossa?branch=master)

PyBossa is an open source platform for crowd-sourcing online (volunteer)
assistance to perform tasks that require human cognition, knowledge or
intelligence (e.g. image classification, transcription, information location
etc). 

![Shuttleworth Foundation Funded](http://daniellombrana.es/static/images/project/shuttleworth_funded.png)

PyBossa was inspired by the [BOSSA](http://bossa.berkeley.edu/) crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks application
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

# See it in Action

PyBossa powers [CrowdCrafting.org](http://crowdcrafting.org/) and [ForestWatchers.net](http://forestwatchers.net)

# Installing and Upgrading

**Important: if you are updating a server, please, be sure to check the
Database Migration scripts, as new changes could introduce new tables,
columns, etc, in the DB model. See the [Migration Section](http://docs.pybossa.com/en/latest/install.html#migrating-the-database-table-structure) from the
documentation**

See [installation instructions](http://docs.pybossa.com/en/latest/install.html).

**NOTE**: The latest version uses M2CRYPTO and the pypi version has a bug that
does not allow you to sign properly RSA keys, however it will install it
perfectly well. For this reason, you will need to install it using this other
version: pip install -e git+https://github.com/Hypernode/M2Crypto#egg=M2Crypto


# Running Tests

Set SQLALCHEMY_DATABASE_TEST_URI e.g.:

```
  SQLALCHEMY_DATABASE_URI = 'postgres://pybossa:pass@localhost/pybossa'
```

Then run the tests (requires nose):

```
  nosetests -v test/
```

# Useful Links

* [Documentation](http://docs.pybossa.com/)
* [Mailing List](http://lists.okfn.org/mailman/listinfo/open-science-dev)

# Contributing

If you want to contribute to the project, please, check the
[CONTRIBUTING file](CONTRIBUTING.md).

It has the instructions to become a contributor.

## Authors

* [Daniel Lombraña González](http://daniellombrana.es) - [Citizen Cyberscience Centre](http://citizencyberscience.net/), [Shuttleworth Fellow](http://www.shuttleworthfoundation.org/fellows/daniel-lombrana/)
* Rufus Pollock - [Open Knowledge Foundation](http://okfn.org/)
* David Anderson - BOINC / Berkeley (via BOSSA)

* [Twitter Bootstrap Icons by Glyphicons](http://http://glyphicons.com/)
* [FontAwesome fonts](http://fortawesome.github.com/Font-Awesome/)
* [GeoLite data by MaxMind](http://www.maxmind.com)

## Copyright / License

Copyright 2013 SF Isle of Man Limited. 

Source Code License: The GNU Affero General Public License, either version 3 of the License
or (at your option) any later version. (see COPYING file)

The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.

Documentation and media is under a Creative Commons Attribution License version
3.
