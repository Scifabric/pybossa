# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [4.0.2](https://github.com/Scifabric/pybossa/compare/v4.0.1...v4.0.2) (2021-03-06)

### [4.0.1](https://github.com/Scifabric/pybossa/compare/v4.0.0...v4.0.1) (2021-03-06)


### Bug Fixes

* remove duplicated method. ([#2020](https://github.com/Scifabric/pybossa/issues/2020)) ([e658e23](https://github.com/Scifabric/pybossa/commit/e658e23a171c1ac3cc355067dd21c2f06fdf3e0a)), closes [#1888](https://github.com/Scifabric/pybossa/issues/1888)
* remove social columns. ([#2019](https://github.com/Scifabric/pybossa/issues/2019)) ([d1ad47b](https://github.com/Scifabric/pybossa/commit/d1ad47b97e53fb902946bec2ebbd795b823f69b1)), closes [#2017](https://github.com/Scifabric/pybossa/issues/2017)

## [4.0.0](https://github.com/Scifabric/pybossa/compare/v3.4.0...v4.0.0) (2021-02-20)


### ⚠ BREAKING CHANGES

* drop support for Flask-Oauth (twitter, facebook and google) (#2010)

* drop support for Flask-Oauth (twitter, facebook and google) ([#2010](https://github.com/Scifabric/pybossa/issues/2010)) ([3df2bc8](https://github.com/Scifabric/pybossa/commit/3df2bc818e21e6e51f82f5ea34fbbbfe7a8fc6fd))

## [3.4.0](https://github.com/Scifabric/pybossa/compare/v3.3.0...v3.4.0) (2021-01-31)


### Features

* **sentinel:** disable sentinel configuration ([#2007](https://github.com/Scifabric/pybossa/issues/2007)) ([27e1450](https://github.com/Scifabric/pybossa/commit/27e1450151d79b6b215fbf23eef47d3c65b9f085))


### Bug Fixes

* add REDIS_URL so rq-dashboard is configured ([#1990](https://github.com/Scifabric/pybossa/issues/1990)) ([029f73e](https://github.com/Scifabric/pybossa/commit/029f73ebf3907a89b1d20448a41c1ebc5ff6935f))

## [3.3.0](https://github.com/Scifabric/pybossa/compare/v3.2.2...v3.3.0) (2020-12-20)


### Features

* **json:** use sqlalchemy_json lib. ([#2004](https://github.com/Scifabric/pybossa/issues/2004)) ([cb9febc](https://github.com/Scifabric/pybossa/commit/cb9febc36e92cc62745173d12e46139704e7a417))


### Bug Fixes

* move inactive users query to settings file. ([#2005](https://github.com/Scifabric/pybossa/issues/2005)) ([7cf0f49](https://github.com/Scifabric/pybossa/commit/7cf0f49874d9d48dd29d5022f98bb5941f05a414))

### [3.2.2](https://github.com/Scifabric/pybossa/compare/v3.2.1...v3.2.2) (2020-11-15)


### Bug Fixes

* **doi:** update the link to Zenodo DOI. ([a770c0b](https://github.com/Scifabric/pybossa/commit/a770c0b0466288abaa4290cc0c0fe77f33aa98d1))
* **vagrant:** remove ansible and use bash. ([#2003](https://github.com/Scifabric/pybossa/issues/2003)) ([997f131](https://github.com/Scifabric/pybossa/commit/997f131c94dbeb28c580449deb72aba100dd67f5))

### [3.2.1](https://github.com/Scifabric/pybossa/compare/v3.2.0...v3.2.1) (2020-10-31)

## [3.2.0](https://github.com/Scifabric/pybossa/compare/v3.1.2...v3.2.0) (2020-10-31)


### Features

* **userprogress:** allow external_uid as a parameter. ([#2000](https://github.com/Scifabric/pybossa/issues/2000)) ([ea3b522](https://github.com/Scifabric/pybossa/commit/ea3b5224bcc889854b79935c0cfa1bae1de39531))


### Bug Fixes

* handle properly unicode error for fixing taskrun issue. ([01a4d1b](https://github.com/Scifabric/pybossa/commit/01a4d1ba3ef11c45d11857dbf19c78f3ee45c405))
* Python3 syntax fixes ([#1981](https://github.com/Scifabric/pybossa/issues/1981)) ([865991f](https://github.com/Scifabric/pybossa/commit/865991f782e139076539595e0b8d2a1821053b06))
* **gdpr:** delete inactive accounts. ([#1979](https://github.com/Scifabric/pybossa/issues/1979)) ([6d3569c](https://github.com/Scifabric/pybossa/commit/6d3569c7dc832f29d6a8a96ac66cac18db8fee48))
* **vagrant:** update playbook and requirements ([#1968](https://github.com/Scifabric/pybossa/issues/1968)) ([3fb38dc](https://github.com/Scifabric/pybossa/commit/3fb38dc3162b12591878e0226e275df0bc29eb63))

### [3.1.3](https://github.com/Scifabric/pybossa/compare/v3.1.2...v3.1.3) (2020-06-06)


### Bug Fixes

* handle properly unicode error for fixing taskrun issue. ([01a4d1b](https://github.com/Scifabric/pybossa/commit/01a4d1ba3ef11c45d11857dbf19c78f3ee45c405))
* Python3 syntax fixes ([#1981](https://github.com/Scifabric/pybossa/issues/1981)) ([865991f](https://github.com/Scifabric/pybossa/commit/865991f782e139076539595e0b8d2a1821053b06))
* **gdpr:** delete inactive accounts. ([#1979](https://github.com/Scifabric/pybossa/issues/1979)) ([6d3569c](https://github.com/Scifabric/pybossa/commit/6d3569c7dc832f29d6a8a96ac66cac18db8fee48))
* **vagrant:** update playbook and requirements ([#1968](https://github.com/Scifabric/pybossa/issues/1968)) ([3fb38dc](https://github.com/Scifabric/pybossa/commit/3fb38dc3162b12591878e0226e275df0bc29eb63))

# Changelog

## v3.0.0 (2019-12-28)

#### Fixes

* (test): use sorted instead of sort()
* (test): use sorted instead of sort()
* (stats): use utc for time.
* (stats): use utc time.
* (test): use UTC time zone in query.
* (test): use b type
#### Others

* (readme): update info.
* (cli): migrate to python3.

## v2.13.1 (2019-10-26)

#### Fixes

* (cve): pillow.
* (README): update badges.
* (redis): revert disable redis.
* (redis): cache was bad handled.
* (tests): return String instead of Response.
* (tests): mock with return string.
* (cve): Use new werkzeug.
* (werkzeug): address CVE issue.
* (settings): add missing settings.
#### Others

* (docker): use custom python2.7 ldap.

## v2.12.2 (2019-06-06)


## v2.12.1 (2019-04-27)


## v2.12.0 (2019-04-10)


## v2.11.1 (2018-11-13)


## v2.11.0 (2018-10-23)


## v2.10.3 (2018-09-04)


## v2.10.0 (2018-08-23)


## v2.9.5 (2018-06-01)


## v2.9.4 (2018-05-18)


## v2.9.3 (2018-05-14)


## v2.9.2 (2018-02-26)


## v2.9.0 (2018-02-06)


## v2.8.0 (2017-10-05)


## v2.7.2 (2017-10-03)


## v2.7.1 (2017-09-27)


## v2.7.0 (2017-09-21)


## v2.6.3 (2017-09-05)


## v2.6.2 (2017-08-28)


## v2.6.1 (2017-08-16)


## v2.6.0 (2017-08-08)


## v2.5.4 (2017-08-07)


## v2.5.2 (2017-06-27)


## v2.5.0 (2017-06-21)


## v2.4.3 (2017-06-15)


## v2.4.2 (2017-06-14)


## v2.4.1 (2017-06-09)


## v2.4.0 (2017-06-08)


## v2.3.7 (2017-05-09)


## v2.3.6 (2017-03-29)


## v2.3.0 (2016-08-03)


## v2.2.0 (2016-05-23)


## v2.0.0 (2016-05-03)


## v1.6.1 (2016-04-07)


## v1.6.0 (2016-04-04)


## v1.5.1 (2016-02-16)


## v1.5.0 (2016-02-08)


## v1.4.1 (2016-01-28)


## v1.4.0 (2016-01-26)


## v1.3.0 (2015-12-17)


## v1.2.2 (2015-12-09)


## v1.2.1 (2015-12-03)


## v1.2.0 (2015-11-24)


## v1.1.3 (2015-11-20)


## v1.1.2 (2015-10-06)


## v1.1.1 (2015-09-30)


## v1.1.0 (2015-09-30)


## v1.0.0 (2015-09-21)


## v0.2.4 (2015-09-21)


## v0.2.3 (2015-08-19)


## v0.2.2 (2015-05-11)


## 2014-08-20 (2014-08-20)


## 2014-08-19 (2014-08-19)


## 2014-08-14 (2014-08-14)


## v0.2.1 (2013-12-04)


## v0.2.0 (2013-11-26)


## v0.1.3 (2013-11-22)


## v0.1.2 (2013-11-22)


## v0.1.1 (2013-10-01)


## v0.1.0 (2013-08-01)
