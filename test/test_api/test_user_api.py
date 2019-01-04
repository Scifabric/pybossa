# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
import json
from default import with_context, Test
from nose.tools import assert_raises
from werkzeug.exceptions import MethodNotAllowed
from pybossa.api.user import UserAPI
from test_api import TestAPI
from pybossa.core import db
from mock import patch, MagicMock

from factories import UserFactory


class TestUserAPI(Test):

    @with_context
    def test_user_get(self):
        """Test API User GET"""
        admin, expected_user, someone = UserFactory.create_batch(3,
                                                                 info=dict(extra='foo',
                                                                 badges=[1,2,3]))
        restricted = UserFactory.create(restrict=True)
        # Test GET all users
        res = self.app.get('/api/user')
        data = json.loads(res.data)
        user = data[0]
        assert len(data) == 3, data
        for datum in data:
            assert sorted(['locale', 'name']) == sorted(list(datum.keys())), list(datum.keys())

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test GETting a specific user by ID
        res = self.app.get('/api/user/%s' % expected_user.id)
        data = json.loads(res.data)
        user = data
        assert user['name'] == expected_user.name, (user['name'],
                                                    expected_user.name)
        assert 'info' not in list(user.keys()), list(user.keys())

        # Test GETting a specific user by ID as owner
        url = '/api/user/%s?api_key=%s' % (expected_user.id,
                                           expected_user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        user = data
        assert user['name'] == expected_user.name, data
        assert 'info' in list(user.keys()), list(user.keys())
        assert user['info']['extra'] == 'foo'
        assert user['info']['badges'] == [1,2,3]

        # Test GETting a specific user by ID as admin
        url = '/api/user/%s?api_key=%s' % (expected_user.id,
                                           admin.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        user = data
        assert user['name'] == expected_user.name, data
        assert 'info' in list(user.keys()), list(user.keys())
        assert user['info']['extra'] == 'foo'
        assert user['info']['badges'] == [1,2,3]

        # Test GETting a specific user by ID as non owner non admin 
        url = '/api/user/%s?api_key=%s' % (expected_user.id,
                                           someone.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        user = data
        assert user['name'] == expected_user.name, data
        assert 'info' not in list(user.keys()), list(user.keys())


        # Test a non-existant ID
        res = self.app.get('/api/user/3434209')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'user', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err

        # Test restricted by anon
        url = '/api/user/%s' % restricted.id
        res = self.app.get(url)
        assert res.status_code == 401, res.status_code

        # As user
        res = self.app.get(url + '?api_key=' + someone.api_key)
        assert res.status_code == 403, res.status_code

        # As admin
        res = self.app.get(url + '?api_key=' + admin.api_key)
        assert res.status_code == 403, res.status_code

        # As same user
        res = self.app.get(url + '?api_key=' + restricted.api_key)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data['id'] == restricted.id

    @with_context
    def test_query_user(self):
        """Test API query for user endpoint works"""
        expected_user, other = UserFactory.create_batch(2)
        restricted = UserFactory.create(restrict=True)
        # When querying with a valid existing field which is unique
        # It should return one correct result if exists
        res = self.app.get('/api/user?name=%s' % expected_user.name)
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert data[0]['name'] == expected_user.name, data
        # Trying to change restrict
        res = self.app.get('/api/user?restrict=true')
        data = json.loads(res.data)
        assert len(data) == 2, data
        for d in data:
            assert d['name'] != restricted.name, d

        # And it should return no results if there are no matches
        res = self.app.get('/api/user?name=Godzilla')
        data = json.loads(res.data)
        assert len(data) == 0, data

        # When querying with a valid existing non-unique field
        res = self.app.get("/api/user?locale=en")
        data = json.loads(res.data)
        # It should return 3 results, as every registered user has locale=en by default
        assert len(data) == 2, data
        # And they should be the correct ones
        assert (data[0]['locale'] == data[1]['locale'] == 'en'
               and data[0] != data[1]), data

        # When querying with multiple valid fields
        res = self.app.get('/api/user?name=%s&locale=en' % expected_user.name)
        data = json.loads(res.data)
        # It should find and return one correct result
        assert len(data) == 1, data
        assert data[0]['name'] == expected_user.name, data
        assert data[0]['locale'] == 'en', data

        # When querying with non-valid fields -- Errors
        res = self.app.get('/api/user?something_invalid=whatever')
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg



    @with_context
    def test_query_restricted_user(self):
        """Test API query for restricted user endpoint works"""
        expected_user, other = UserFactory.create_batch(2, restrict=True)
        # When querying with a valid existing field which is unique
        # It should return one correct result if exists
        res = self.app.get('/api/user?name=%s' % expected_user.name)
        data = json.loads(res.data)
        assert len(data) == 0, data
        # And it should return no results if there are no matches
        res = self.app.get('/api/user?name=Godzilla')
        data = json.loads(res.data)
        assert len(data) == 0, data

        # When querying with a valid existing non-unique field
        res = self.app.get("/api/user?locale=en")
        data = json.loads(res.data)
        # It should return 3 results, as every registered user has locale=en by default
        assert len(data) == 0, data

        # When querying with multiple valid fields
        res = self.app.get('/api/user?name=%s&locale=en' % expected_user.name)
        data = json.loads(res.data)
        # It should find and return one correct result
        assert len(data) == 0, data

        # When querying with non-valid fields -- Errors
        res = self.app.get('/api/user?something_invalid=whatever')
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # As other user
        # When querying with a valid existing field which is unique
        # It should return one correct result if exists
        res = self.app.get('/api/user?name=%s&api_key=%s' % (expected_user.name,
                                                           other.api_key))
        data = json.loads(res.data)
        assert len(data) == 0, data
        # And it should return no results if there are no matches
        res = self.app.get('/api/user?name=Godzilla&api_key=%s' + other.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # When querying with a valid existing non-unique field
        res = self.app.get("/api/user?locale=en&api_key=" + other.api_key)
        data = json.loads(res.data)
        # It should return 3 results, as every registered user has locale=en by default
        assert len(data) == 0, data

        # When querying with multiple valid fields
        res = self.app.get('/api/user?name=%s&locale=en&api_key=%s' %
                           (expected_user.name, other.api_key))
        data = json.loads(res.data)
        # It should find and return one correct result
        assert len(data) == 0, data

        # When querying with non-valid fields -- Errors
        res = self.app.get('/api/user?something_invalid=whatever&api_key=' +
                           other.api_key)
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # As same user
        # When querying with a valid existing field which is unique
        # It should return one correct result if exists
        res = self.app.get('/api/user?name=%s&api_key=%s' % (expected_user.name,
                                                           expected_user.api_key))
        data = json.loads(res.data)
        assert len(data) == 0, data
        # And it should return no results if there are no matches
        res = self.app.get('/api/user?name=Godzilla&api_key=' + expected_user.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # When querying with a valid existing non-unique field
        res = self.app.get("/api/user?locale=en&api_key=" + expected_user.api_key)
        data = json.loads(res.data)
        # It should return 3 results, as every registered user has locale=en by default
        assert len(data) == 0, data

        # When querying with multiple valid fields
        res = self.app.get('/api/user?name=%s&locale=en&api_key=%s' %
                           (expected_user.name, expected_user.api_key))
        data = json.loads(res.data)
        # It should find and return one correct result
        assert len(data) == 0, data

        # When querying with non-valid fields -- Errors
        res = self.app.get('/api/user?something_invalid=whatever&api_key=' +
                           expected_user.api_key)
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

    @with_context
    def test_user_not_allowed_actions_anon(self):
        """Test POST, PUT and DELETE for ANON actions are not allowed for user
        in the API"""
        user = UserFactory.create()
        url = 'api/user'
        res = self.app.post(url, data=json.dumps(user.to_public_json()))
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data

        url += '/%s' % user.id
        res = self.app.put(url, data=json.dumps(dict(name='new')))
        assert res.status_code == 401, res.data

        res = self.app.delete(url)
        assert res.status_code == 405, res.status_code

    @with_context
    @patch('pybossa.api.api_base.caching')
    def test_user_not_allowed_actions_user(self, caching_mock):
        """Test POST, PUT and DELETE for USER actions are not allowed for user
        in the API"""
        clean_user_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_user_mock)
        admin = UserFactory.create()
        auth = UserFactory.create()
        user = UserFactory.create()
        url = 'api/user'
        res = self.app.post(url + '?api_key=%s' % auth.api_key,
                            data=json.dumps(user.to_public_json()))
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data

        # Update another user
        url += '/%s' % user.id
        res = self.app.put(url + '?api_key=%s' % auth.api_key,
                           data=json.dumps(dict(name='new')))
        assert res.status_code == 403, res.data

        res = self.app.delete(url + '?apikey=%s' % auth.api_key)
        assert res.status_code == 405, res.status_code

        # Update the same user
        url = 'api/user/%s' % auth.id
        res = self.app.put(url + '?api_key=%s' % auth.api_key,
                           data=json.dumps(dict(name='new')))
        data = json.loads(res.data)
        assert res.status_code == 200, res.data
        assert data['name'] == 'new', data
        clean_user_mock.assert_called_with(data['id'])

    @with_context
    @patch('pybossa.api.api_base.caching')
    def test_user_not_allowed_actions_admin(self, caching_mock):
        """Test POST, PUT and DELETE for ADMIN actions are not allowed for user
        in the API"""

        clean_user_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_user_mock)

        admin = UserFactory.create()
        auth = UserFactory.create()
        user = UserFactory.create()
        url = 'api/user'
        res = self.app.post(url + '?api_key=%s' % admin.api_key,
                            data=json.dumps(user.to_public_json()))
        data = json.loads(res.data)
        assert res.status_code == 405, res.status_code
        assert data['status_code'] == 405, data

        # Update another user
        url += '/%s' % user.id
        new_info = user.info
        new_info['foo'] = 'bar'
        res = self.app.put(url + '?api_key=%s' % admin.api_key,
                           data=json.dumps(dict(name='new', info=new_info)))
        data = json.loads(res.data)
        assert res.status_code == 200, res.data
        assert data['name'] == 'new', data
        assert data['info']['foo'] == 'bar', data
        clean_user_mock.assert_called_with(data['id'])

        res = self.app.delete(url + '?apikey=%s' % auth.api_key)
        assert res.status_code == 405, res.status_code

        # Update the same user
        url = 'api/user/%s' % admin.id
        res = self.app.put(url + '?api_key=%s' % admin.api_key,
                           data=json.dumps(dict(name='newadmin')))
        data = json.loads(res.data)
        assert res.status_code == 200, res.data
        assert data['name'] == 'newadmin', data
        clean_user_mock.assert_called_with(data['id'])


    @with_context
    def test_privacy_mode_user_get(self):
        """Test API user queries for privacy mode"""
        admin = UserFactory.create()
        user = UserFactory.create()
        # Add user with fullname 'Public user', privacy mode disabled
        user_with_privacy_disabled = UserFactory.create(email_addr='public@user.com',
                                    name='publicUser', fullname='Public user',
                                    privacy_mode=False)
        # Add user with fullname 'Private user', privacy mode enabled
        user_with_privacy_enabled = UserFactory.create(email_addr='private@user.com',
                                    name='privateUser', fullname='Private user',
                                    privacy_mode=True)

        # With no API-KEY
        # User with privacy disabled
        res = self.app.get('/api/user/3')
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/4')
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should not be returned
        assert 'fullname' not in user_with_privacy_enabled, data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user')
        data = json.loads(res.data)
        user_with_privacy_disabled = data[2]
        user_with_privacy_enabled = data[3]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert 'fullname' not in user_with_privacy_enabled, data

        # With a non-admin API-KEY
        # User with privacy disabled
        res = self.app.get('/api/user/3?api_key=' + user.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/4?api_key=' + user.api_key)
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should not be returned
        assert 'fullname' not in user_with_privacy_enabled, data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user?api_key=' + user.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data[2]
        user_with_privacy_enabled = data[3]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert 'fullname' not in user_with_privacy_enabled, data

        # Admin API-KEY should be able to retrieve every field in user
        res = self.app.get('/api/user/3?api_key=' + admin.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_disabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        # User with privacy enabled
        res = self.app.get('/api/user/4?api_key=' + admin.api_key)
        data = json.loads(res.data)
        user_with_privacy_enabled = data
        # When checking a public field it should be returned
        assert user_with_privacy_enabled['locale'] == 'en', data
        # When checking a private field it should be returned too
        assert user_with_privacy_enabled['fullname'] == 'Private user', data
        # Users with privacy enabled and disabled, mixed together
        res = self.app.get('/api/user?api_key=' + admin.api_key)
        data = json.loads(res.data)
        user_with_privacy_disabled = data[2]
        user_with_privacy_enabled = data[3]
        assert user_with_privacy_disabled['locale'] == 'en', data
        assert user_with_privacy_disabled['fullname'] == 'Public user', data
        assert user_with_privacy_enabled['locale'] == 'en', data
        assert user_with_privacy_enabled['fullname'] == 'Private user', data


    @with_context
    def test_privacy_mode_user_queries(self):
        """Test API user queries for privacy mode with private fields in query
        """
        admin = UserFactory.create()
        user = UserFactory.create()
        # Add user with fullname 'Public user', privacy mode disabled
        user_with_privacy_disabled = UserFactory(email_addr='public@user.com',
                                    name='publicUser', fullname='User',
                                    privacy_mode=False)
        # Add user with fullname 'Private user', privacy mode enabled
        user_with_privacy_enabled = UserFactory(email_addr='private@user.com',
                                    name='privateUser', fullname='User',
                                    info=dict(container=1, avatar='png',
                                             avatar_url='1png',extra='badge1.png'),
                                    privacy_mode=True)

        # When querying with private fields
        query = 'api/user?fullname=User'
        # with no API-KEY, no user with privacy enabled should be returned,
        # even if it matches the query
        res = self.app.get(query)
        data = json.loads(res.data)
        assert len(data) == 1, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user
        assert 'email_addr' not in list(public_user.keys()), public_user
        assert 'id' not in list(public_user.keys()), public_user
        assert 'info' not in list(public_user.keys()), public_user

        # with a non-admin API-KEY, the result should be the same
        res = self.app.get(query + '&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user
        assert 'email_addr' not in list(public_user.keys()), public_user
        assert 'id' not in list(public_user.keys()), public_user
        assert 'info' not in list(public_user.keys()), public_user

        # with an admin API-KEY, all the matching results should be returned
        res = self.app.get(query + '&api_key=' + admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 2, data
        public_user = data[0]
        assert public_user['name'] == 'publicUser', public_user
        private_user = data[1]
        assert private_user['name'] == 'privateUser', private_user
        assert private_user['email_addr'] == user_with_privacy_enabled.email_addr, private_user
        assert private_user['id'] == user_with_privacy_enabled.id, private_user
        assert private_user['info'] == user_with_privacy_enabled.info, private_user
