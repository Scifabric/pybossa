# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
import json
from base import model, Fixtures, db
from nose.tools import assert_equal, assert_raises
from test_api import HelperAPI
from pybossa.api.token import TokenAPI
from werkzeug.exceptions import MethodNotAllowed



class TestTaskrunAPI(HelperAPI):

    #checkear que el endpoint está bien.
    #que los formatos de los tokens que devuelve son los apropiados para cada provider


    def test_not_allowed_methods(self):
        """Test POST, DELETE, PUT methods are not allowed for resource token"""
        token_api_instance = TokenAPI()

        post_response = self.app.post('/api/token')
        assert post_response.status_code == 405, post_response.status_code
        assert_raises(MethodNotAllowed, token_api_instance.post)
        delete_response = self.app.delete('/api/token')
        assert delete_response.status_code == 405, delete_response.status_code
        assert_raises(MethodNotAllowed, token_api_instance.delete)
        put_response = self.app.put('/api/token')
        assert put_response.status_code == 405, put_response.status_code
        assert_raises(MethodNotAllowed, token_api_instance.put)


    def test_get_all_tokens_anonymous_user(self):
        """Test anonymous users are unauthorized to request their tokens"""

        # Anonymoues users should be unauthorized, no matter which kind of token are requesting
        res = self.app.get('/api/token')
        err = json.loads(res.data)

        assert res.status_code == 401, err
        assert err['status'] == 'failed', err
        assert err['status_code'] == 401, err
        assert err['exception_cls'] == 'Unauthorized', err
        assert err['target'] == 'token', err

    def test_get_specific_token_anonymous_user(self):
        """Test anonymous users are unauthorized to request any of their tokens"""

        res = self.app.get('/api/token/twitter')
        err = json.loads(res.data)

        assert res.status_code == 401, err
        assert err['status'] == 'failed', err
        assert err['status_code'] == 401, err
        assert err['exception_cls'] == 'Unauthorized', err
        assert err['target'] == 'token', err

    def test_get_all_tokens_authenticated_user(self):
        """Test authenticated user is able to retrieve all his tokens"""

        user = db.session.query(model.User).get(2)
        twitter_token = {'oauth_token': 'token-for-%s' % user.name,
                         'oauth_token_secret': 'secret-for-%s' % user.name}
        facebook_token = {'oauth_token': 'facebook_token'}
        google_token = {'oauth_token': 'google_token'}
        user.info['twitter_token'] = twitter_token
        user.info['facebook_token'] = facebook_token
        user.info['google_token'] = google_token
        db.session.commit()

        res = self.app.get('api/token?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)

        for provider in TokenAPI.oauth_providers:
            token_name = '%s_token' % provider
            assert data.get(token_name) is not None, data

    def test_get_all_existing_tokens_authenticated_user(self):
        """Test if a user lacks one of the valid tokens, it won't be retrieved"""

        user = db.session.query(model.User).get(2)
        twitter_token = {'oauth_token': 'token-for-%s' % user.name,
                         'oauth_token_secret': 'secret-for-%s' % user.name}
        facebook_token = {'oauth_token': 'facebook_token'}
        google_token = {'oauth_token': 'google_token'}
        user.info['twitter_token'] = twitter_token
        user.info['facebook_token'] = facebook_token
        db.session.commit()

        res = self.app.get('api/token?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)

        assert data.get('twitter_token') is not None, data
        assert data.get('facebook_token') is not None, data
        assert data.get('google_token') is None, data

    def test_get_existing_token_authenticated_user(self):
        """Test authenticated user retrieves a given existing token"""

        user = db.session.query(model.User).get(2)
        twitter_token = {'oauth_token': 'token-for-%s' % user.name,
                         'oauth_token_secret': 'secret-for-%s' % user.name}
        facebook_token = {'oauth_token': 'facebook_token'}
        google_token = {'oauth_token': 'google_token'}
        user.info['twitter_token'] = twitter_token
        user.info['facebook_token'] = facebook_token
        user.info['google_token'] = google_token
        db.session.commit()

        # If the token exists, it should be retrieved
        res = self.app.get('/api/token/twitter?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)

        assert data.get('twitter_token') is not None, data
        assert data.get('twitter_token')['oauth_token'] == 'token-for-%s' % user.name
        assert data.get('twitter_token')['oauth_token_secret'] == 'secret-for-%s' % user.name
        # And no other tokens should
        assert data.get('facebook_token') is None, data

    def test_get_non_existing_token_authenticated_user(self):
        """Test authenticated user cannot get non-existing tokens"""

        user_without_tokens = db.session.query(model.User).get(3)

        res = self.app.get('/api/token/twitter?api_key=' + Fixtures.api_key_2)
        error = json.loads(res.data)

        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'GET', error
        assert error['target'] == 'token', error
        assert error['exception_cls'] == 'NotFound', error

    def test_get_non_valid_token(self):
        """Test authenticated user cannot get non-valid tokens"""

        res = self.app.get('/api/token/non-valid?api_key=' + Fixtures.api_key)
        error = json.loads(res.data)

        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'GET', error
        assert error['target'] == 'token', error
        assert error['exception_cls'] == 'NotFound', error








