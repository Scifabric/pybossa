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
from nose.tools import assert_raises
from werkzeug.exceptions import MethodNotAllowed
from pybossa.api.user import UserAPI
from test_api import HelperAPI


class TestUserAPI(HelperAPI):

    def test_user_get(self):
        """Test API User GET"""
        # Test a GET all users
        res = self.app.get('/api/user')
        data = json.loads(res.data)
        user = data[0]
        assert len(data) == 3, data
        assert user['name'] == 'root', data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test GETting a specific user by ID
        res = self.app.get('/api/user/1')
        data = json.loads(res.data)
        user = data
        assert user['name'] == 'root', data

        # Test a non-existant ID
        res = self.app.get('/api/user/3434209')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'user', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err


    def test_query_user(self):
        """Test API query for user endpoint works"""

        # When querying with a valid existing field which is unique
        # It should return one correct result if exists
        res = self.app.get('/api/user?name=root')
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert data[0]['name'] == 'root', data
        # And it should return no results if there are no matches
        res = self.app.get('/api/user?name=Godzilla')
        data = json.loads(res.data)
        assert len(data) == 0, data

        # When querying with a valid existing non-unique field
        res = self.app.get("/api/user?locale=en")
        data = json.loads(res.data)
        # It should return 3 results, as every registered user has locale=en by default
        assert len(data) == 3, data
        # And they should be the correct ones
        assert (data[0]['locale'] == data[1]['locale'] == 'en'
               and data[0] != data[1]), data

        # When querying with multiple valid fields
        res = self.app.get('/api/user?name=root&locale=en')
        data = json.loads(res.data)
        # It should find and return one correct result
        assert len(data) == 1, data
        assert data[0]['name'] == 'root', data
        assert data[0]['locale'] == 'en', data

        # When querying with non-valid fields -- Errors
        res = self.app.get('/api/user?something_invalid=whatever')
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg


    def test_user_not_allowed_actions(self):
        """Test POST, PUT and DELETE actions are not allowed for user
        in the API"""

        user_api_instance = UserAPI()
        post_response = self.app.post('/api/user')
        assert post_response.status_code == 405, post_response.status_code
        assert_raises(MethodNotAllowed, user_api_instance.post)
        delete_response = self.app.delete('/api/user')
        assert delete_response.status_code == 405, delete_response.status_code
        assert_raises(MethodNotAllowed, user_api_instance.delete)
        put_response = self.app.put('/api/user')
        assert put_response.status_code == 405, put_response.status_code
        assert_raises(MethodNotAllowed, user_api_instance.put)


    def test_privacy_mode_user_get(self):
        """Test API user queries for privacy mode"""

        # Add user with fullname 'Public user', privacy mode disabled
        user_with_privacy_disabled = model.User(email_addr='public@user.com',
                                    name='publicUser', fullname='Public user',
                                    privacy_mode=False)
        db.session.add(user_with_privacy_disabled)
        # Add user with fullname 'Private user', privacy mode enabled
        user_with_privacy_enabled = model.User(email_addr='private@user.com',
                                    name='privateUser', fullname='Private user',
                                    privacy_mode=True)
        db.session.add(user_with_privacy_enabled)
        db.session.commit()

        # With no API-KEY
        # User with privacy disabled
        res = self.app.get('/api/user/4')
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/5')
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should not be returned
        assert 'fullname' not in user_with_privacy_enabled, data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user')
        data = json.loads(res.data)
        user_with_privacy_disabled = data[3]
        user_with_privacy_enabled = data[4]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert 'fullname' not in user_with_privacy_enabled, data

        # With a non-admin API-KEY
        # User with privacy disabled
        res = self.app.get('/api/user/4?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/5?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should not be returned
        assert 'fullname' not in user_with_privacy_enabled, data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user?api_key=' + Fixtures.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data[3]
        user_with_privacy_enabled = data[4]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert 'fullname' not in user_with_privacy_enabled, data

        # Admin API-KEY should be able to retrieve every field in user
        res = self.app.get('/api/user/4?api_key=' + Fixtures.root_api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/5?api_key=' + Fixtures.root_api_key)
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_enabled['fullname'] == 'Private user', data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user?api_key=' + Fixtures.root_api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data[3]
        user_with_privacy_enabled = data[4]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert user_with_privacy_enabled['fullname'] == 'Private user', data


    def test_privacy_mode_user_queries(self):
        """Test API user queries for privacy mode with private fields in query
        """

        # Add user with fullname 'Public user', privacy mode disabled
        user_with_privacy_disabled = model.User(email_addr='public@user.com',
                                    name='publicUser', fullname='User',
                                    privacy_mode=False)
        db.session.add(user_with_privacy_disabled)
        # Add user with fullname 'Private user', privacy mode enabled
        user_with_privacy_enabled = model.User(email_addr='private@user.com',
                                    name='privateUser', fullname='User',
                                    privacy_mode=True)
        db.session.add(user_with_privacy_enabled)
        db.session.commit()

        # When querying with private fields
        query = 'api/user?fullname=User'
        # with no API-KEY, no user with privacy enabled should be returned,
        # even if it matches the query
        res = self.app.get(query)
        data = json.loads(res.data)
        assert len(data) == 1, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user

        # with a non-admin API-KEY, the result should be the same
        res = self.app.get(query + '&api_key=' + Fixtures.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user

        # with an admin API-KEY, all the matching results should be returned
        res = self.app.get(query + '&api_key=' + Fixtures.root_api_key)
        data = json.loads(res.data)
        assert len(data) == 2, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user
        private_user = data[1]
        assert private_user['name'] == 'privateUser', private_user
