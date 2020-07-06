# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
from flask_oauthlib.client import OAuth
from tests.sp.base import CERTIFICATE, PRIVATE_KEY

class Twitter(object):

    """Class Twitter to enable Twitter signin."""

    def __init__(self, app=None):
        """Init method."""
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Init app using factories."""
        self.oauth = OAuth().remote_app(
            'twitter',
            base_url='https://api.twitter.com/1/',
            request_token_url='https://api.twitter.com/oauth/request_token',
            access_token_url='https://api.twitter.com/oauth/access_token',
            authorize_url='https://api.twitter.com/oauth/authenticate',
            consumer_key=app.config['TWITTER_CONSUMER_KEY'],
            consumer_secret=app.config['TWITTER_CONSUMER_SECRET'])


class Facebook(object):

    """Class Facebook to enable Facebook signin."""

    def __init__(self, app=None):
        """Init method."""
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Init app using factories pattern."""
        self.oauth = OAuth().remote_app(
            'facebook',
            base_url='https://graph.facebook.com/',
            request_token_url=None,
            access_token_url='/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            consumer_key=app.config['FACEBOOK_APP_ID'],
            consumer_secret=app.config['FACEBOOK_APP_SECRET'],
            request_token_params={'scope': 'email'})


class Google(object):

    """Class Google to enable Google signin."""

    def __init__(self, app=None):
        """Init method."""
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Init app using factories pattern."""
        self.oauth = OAuth().remote_app(
            'google',
            base_url='https://www.googleapis.com/oauth2/v1/',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            request_token_url=None,
            request_token_params={'scope': 'profile email'},
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_method='POST',
            consumer_key=app.config['GOOGLE_CLIENT_ID'],
            consumer_secret=app.config['GOOGLE_CLIENT_SECRET'])

class Mkplay(object):

    """Class Google to enable Google signin."""

    def __init__(self, app=None):
        """Init method."""
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Init app using factories pattern."""
        # self.oauth = OAuth().remote_app(
        #     'google',
        #     base_url='https://www.googleapis.com/oauth2/v1/',
        #     authorize_url='https://accounts.google.com/o/oauth2/auth',
        #     request_token_url=None,
        #     request_token_params={'scope': 'profile email'},
        #     access_token_url='https://accounts.google.com/o/oauth2/token',
        #     access_token_method='POST',
        #     consumer_key=app.config['GOOGLE_CLIENT_ID'],
        #     consumer_secret=app.config['GOOGLE_CLIENT_SECRET'])
        app.config['SAML2_IDENTITY_PROVIDERS'] = [
            {
                'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
                'OPTIONS': {
                    'display_name': 'mkplaydevvm',
                    # 'entity_id': 'http://localhost:8000/saml/metadata.xml',
                    # 'sso_url': 'http://localhost:8000/saml/login/',
                    # 'slo_url': 'http://localhost:8000/saml/logout/',
                    # 'certificate': IDP_CERTIFICATE,
                    'entity_id': 'https://srishti117.mykaarma.dev/simplesaml/saml2/idp/metadata.php',
                    'sso_url': 'https://srishti117.mykaarma.dev/simplesaml/saml2/idp/SSOService.php',
                    'slo_url': 'https://srishti117.mykaarma.dev/simplesaml/saml2/idp/SingleLogoutService.php',
                    # 'certificate': 'https://github.com/mykaarma/mk-login-saml/blob/master/samlconfig/devvm/cert/accounts.dev.mykaarma.com.crt',
                    'certificate':'MIIErTCCA5WgAwIBAgIJALwyYqHztbdZMA0GCSqGSIb3DQEBBQUAMIGVMQswCQYDVQQGEwJVUzELMAkGA1UECBMCQ0ExFDASBgNVBAcTC0xvcyBBbmdlbGVzMREwDwYDVQQKEwhteUthYXJtYTESMBAGA1UECxMJS2FhcmEgTExDMREwDwYDVQQDEwhteUthYXJtYTEpMCcGCSqGSIb3DQEJARYabW91bGkua2F0aHVsYUBteWthYXJtYS5jb20wHhcNMTcwNjEwMjIxNTUxWhcNMjcwNjEwMjIxNTUxWjCBlTELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAkNBMRQwEgYDVQQHEwtMb3MgQW5nZWxlczERMA8GA1UEChMIbXlLYWFybWExEjAQBgNVBAsTCUthYXJhIExMQzERMA8GA1UEAxMIbXlLYWFybWExKTAnBgkqhkiG9w0BCQEWGm1vdWxpLmthdGh1bGFAbXlrYWFybWEuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3x1HaYfdySj3vM6j/EwVD3lLkgqBrrIZEaRFI5ej7B3h7lTpklhd5KI48BQv0F0BCK3Cb3vYqQgxLYHh3UvTY1IoGhNVq3XHyKe60b56Q331b6CIeLiI3wEEbrbW0w9FvQkYFNmuwR7G0elIGYtC1QOL7A2JBs1a3Dw+D1LAHQzk8PFWYpXCdkKrsQnh3rk09Ol9BfyCl5urbe0v0Mv9MBxAIbJb5M7P9W3K2/9sNSEaRSwuFNOCsFCkoNBrd/fo6p6ar48d6Gr5GdHml7Nvljlx6Xx0aQ5JrHoLXGVbH+YDVKNOzUt5AOLHe0Fs4BoBDgjOoFJ7kT2gFTHzEECa1wIDAQABo4H9MIH6MB0GA1UdDgQWBBTjNfProDO5wx/FiRuWBKhWHbVTtjCBygYDVR0jBIHCMIG/gBTjNfProDO5wx/FiRuWBKhWHbVTtqGBm6SBmDCBlTELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAkNBMRQwEgYDVQQHEwtMb3MgQW5nZWxlczERMA8GA1UEChMIbXlLYWFybWExEjAQBgNVBAsTCUthYXJhIExMQzERMA8GA1UEAxMIbXlLYWFybWExKTAnBgkqhkiG9w0BCQEWGm1vdWxpLmthdGh1bGFAbXlrYWFybWEuY29tggkAvDJiofO1t1kwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAc8bwbf97ccZoa3aaBS8WTEjbLrztA4iAKctj10LcSn63BA7gCgry2MLNDwzPIWt2B4BqfZRjfFGn3tuDcGhrW0O6LigxMlja0MYV9bbnxH+nTdfVLTJfCAJQtgR/NEnh2xel5/32YHYc1C/I8jx+jg5x5/9p//laFQPyCF6YwvaZwOjrFQTbLrA/vpcIQ/lxK876Q22LZsZWJfrqalE7mO8rLIeAt1QZOeBHv5Vge3vbqsaLKTCCU1fY0FKE++5jLlaYl6MPOpJAZ+6u7uKFJ094+IER48gAgCAiNj4vOPV024SFy2m3W/HKyGeelcuaO8Kel/FNBpC+vljcD5CvFg=='
                },
            },
        ]
        
        app.config['SAML2_SP'] = {
            'certificate': CERTIFICATE,
            'private_key': PRIVATE_KEY,
        }
        print("APP INITIALISED")
        

class Flickr(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):  # pragma: no cover
        from flask import session
        self.app = app
        self.oauth = OAuth().remote_app(
            'flickr',
            request_token_url='https://www.flickr.com/services/oauth/request_token',
            access_token_url='https://www.flickr.com/services/oauth/access_token',
            authorize_url='https://www.flickr.com/services/oauth/authorize',
            consumer_key=app.config['FLICKR_API_KEY'],
            consumer_secret=app.config['FLICKR_SHARED_SECRET'],
            access_token_method='GET')
