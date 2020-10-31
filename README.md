[![Scifabric](https://img.shields.io/badge/made%20by-scifabric-blue.svg)](https://scifabric.com/)
[![Build Status](https://circleci.com/gh/Scifabric/pybossa/tree/master.svg?style=shield)](https://circleci.com/gh/Scifabric/pybossa)
 [![Coverage Status](https://img.shields.io/coveralls/Scifabric/pybossa.svg)](https://coveralls.io/r/Scifabric/pybossa?branch=master)
[![Documentation](https://readthedocs.org/projects/pybossa/badge/?version=latest)](http://docs.pybossa.com) [![License](http://img.shields.io/badge/license-agplv3-b75bb6.svg)](http://www.gnu.org/licenses/agpl-3.0.html) [![Join the chat at https://gitter.im/Scifabric/pybossa](https://badges.gitter.im/Scifabric/pybossa.svg)](https://gitter.im/Scifabric/pybossa?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3882334.svg)](https://doi.org/10.5281/zenodo.3882334)
[![Scifabric's Patreon](https://img.shields.io/badge/support%20us%20on-patreon-orange.svg)](https://www.patreon.com/bePatron?u=4979179)

# What is PYBOSSA?

PYBOSSA is a technology built by [Scifabric](https://scifabric.com), for crowdsourcing or citizen science platforms.

PYBOSSA is an extremely flexible and versatile technology with a multitude of applications that
adapt to each specific case facilitating many of the daily tasks that take place in research
environments such as museums, art galleries, heritage institutions, libraries of any kind, market
research companies, hospitals, universities and all those organisations that manage data or require
information from their customers/users -such as airports, shopping malls, banks, hotel chains, etc.

PYBOSSA’s simplicity consists in its easy adjustment to any areas using any of the available
templates, this way every customer can then adapt it to their own needs.

PYBOSSA integrates with other data collection products such as Amazon S3, Twitter, Youtube,
Google Spreadsheets, Flickr, Raspberry Pi, etc. Through all these integrations
PYBOSSA allows data capture for further analysis made by users in a transparent and easy way.

- 📘 Documentation: [https://docs.pybossa.com](https://docs.pybossa.com)
- 🎬 Video: [Intro](https://www.youtube.com/watch?v=oH8fJAhRDJM)
- 🐦 Twitter: [@PyBossa](https://twitter.com/pybossa)
- 💬 Chat: [Gitter](https://gitter.im/Scifabric/pybossa)
- 📦 [PYBOSSA extras](https://github.com/Scifabric/)
- 👉 [Play with PYBOSSA online](https://crowdcrafting.org)

# PYBOSSA for python 3

PYBOSSA runs in python >= 3.6. While 3.8 has been released recently, it needs testing before officially support it.

If you have a python2.7 server, please, checkout the python2.7 branch and use that one for your server.

## Get professional support

You can hire us to help you with your PYBOSSA project or server (specially for python 2.7). Go to our website, and [contact us](https://scifabric.com/).


### Supporting PYBOSSA

PYBOSSA is an open source project. Its ongoing development is made possible thanks to the support by these awesome
[backers](https://github.com/Scifabric/pybossa/blob/master/BACKERS.md). If you'd like to join them, check out
[Scifabric's Patreon campaign](https://www.patreon.com/scifabric).


Actividad subvencionada por el Ministerio de Educación, Cultura y Deporte

![Ministerio de Educación, Cultura y Deporte](http://i.imgur.com/4ShmIt1.jpg)


# See it in Action

PYBOSSA powers [Nightup](https://nightup.icfo.eu/) and [MicroPast](http://crowdsourced.micropasts.org/), [LibCrowds](https://www.libcrowds.com/), [Lost at Night](https://lostatnight.org/) and many more projects.

For a full list of PYBOSSA projects, check our [case studies](https://scifabric.com/) and [blog](https://scifabric.com/blog/).

# Installing and Upgrading

**Important: if you are updating a server, please, be sure to check the
Database Migration scripts, as new changes could introduce new tables,
columns, etc, in the DB model. See the [Updating Section](https://docs.pybossa.com/installation/guide/#updating-pybossa) from the documentation**

See [installation instructions](https://docs.pybossa.com/installation/gettingstarted/).

# Testing

## Unit testing

Just run:

```
  nosetests test/
```

## Browser testing

[![BrowserStack](http://i.imgur.com/Pg0utrk.png)](http://browserstack.com/)

Thanks to the support of [BrowserStack](http://browserstack.com/) we can do real cross browser testing on multiple desktop and mobile platforms.

# Contributing

If you want to contribute to the project, please, check the
[CONTRIBUTING file](CONTRIBUTING.md).

It has the instructions to become a contributor.

## Pull requests

Please, use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) when sending your pull requests, as well as tests and documentation for your fix or improvement. It will help us to fully understand what you are solving or improving, and it will let the community know what's going one with the new feature or fix.

# Changelog

Read [CHANGELOG](CHANGELOG.md)

## Acknowledgments

* [Citizen Cyberscience Centre](http://www.citizencyberlab.org/)
* [Open Knowledge Foundation](http://okfn.org/)
* [FontAwesome fonts](http://fortawesome.github.com/Font-Awesome/)
* [GeoLite data by MaxMind](http://www.maxmind.com)
* [yaycryptopan](https://github.com/keiichishima/yacryptopan)

Special thanks to Shuttleworth Foundations for funding us and their true support:
* [Shuttleworth Foundation](https://www.shuttleworthfoundation.org/)
![Shuttleworth Foundation Funded](http://pybossa.com/assets/img/shuttleworth-funded.png)

PYBOSSA was inspired by the [BOSSA](http://bossa.berkeley.edu/) crowdsourcing engine but is written in
python (hence the name!). It can be used for any distributed tasks project
but was initially developed to help scientists and other researchers
crowd-source human problem-solving skills!

## Copyright / License

Copyright 2020 [Scifabric LTD](https://scifabric.com).

Source Code License: The GNU Affero General Public License, either version 3 of the License
or (at your option) any later version. (see COPYING file)

The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.

Documentation and media is under a Creative Commons Attribution License version
3.
