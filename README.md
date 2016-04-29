[![Build
Status](https://travis-ci.org/PyBossa/pybossa.svg?branch=master)](https://travis-ci.org/PyBossa/pybossa) [![Code Health](https://landscape.io/github/PyBossa/pybossa/master/landscape.svg)](https://landscape.io/github/PyBossa/pybossa/master) [![Coverage
Status](https://img.shields.io/coveralls/PyBossa/pybossa.svg)](https://coveralls.io/r/PyBossa/pybossa?branch=master)
[![Documentation](https://readthedocs.org/projects/pybossa/badge/?version=latest)](http://docs.pybossa.com) [![License](http://img.shields.io/badge/license-agplv3-b75bb6.svg)](http://www.gnu.org/licenses/agpl-3.0.html) [![Slack](http://slackin.crowdcrafting.org/badge.svg)](http://slackin.crowdcrafting.org) 
[![DOI](https://zenodo.org/badge/12868/PyBossa/pybossa.svg)](https://zenodo.org/badge/latestdoi/12868/PyBossa/pybossa)



PyBossa is an open source platform for crowd-sourcing online (volunteer)
assistance to perform tasks that require human cognition, knowledge or
intelligence (e.g. image classification, transcription, information location
etc).

![Shuttleworth Foundation Funded](http://pybossa.com/assets/img/shuttleworth-funded.png)

PyBossa was inspired by the [BOSSA](http://bossa.berkeley.edu/) crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks project
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

# See it in Action

PyBossa powers [Crowdcrafting.org](http://crowdcrafting.org/) and [MicroPast](http://crowdsourced.micropasts.org/) a joint project by British Museum and University College of London.

# Installing and Upgrading

**Important: if you are updating a server, please, be sure to check the
Database Migration scripts, as new changes could introduce new tables,
columns, etc, in the DB model. See the [Updating Section](http://docs.pybossa.com/en/latest/install.html#updating-pybossa) from the
documentation**

See [installation instructions](http://docs.pybossa.com/en/latest/installing_pybossa.html).

# Running Tests

Just run the following command:

```
  nosetests test/
```

# Useful Links

* [Documentation](http://docs.pybossa.com/)
* [Mailing List](http://lists.okfn.org/mailman/listinfo/open-science-dev)

# Contributing

If you want to contribute to the project, please, check the
[CONTRIBUTING file](CONTRIBUTING.md).

It has the instructions to become a contributor.

## Acknowledgments

* [Open Knowledge Foundation](http://okfn.org/)
* [FontAwesome fonts](http://fortawesome.github.com/Font-Awesome/)
* [GeoLite data by MaxMind](http://www.maxmind.com)

## Copyright / License

Copyright 2015 [SciFabric LTD](http://scifabric.com).

Source Code License: The GNU Affero General Public License, either version 3 of the License
or (at your option) any later version. (see COPYING file)

The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.

Documentation and media is under a Creative Commons Attribution License version
3.
