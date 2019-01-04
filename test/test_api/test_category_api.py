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
from default import db, with_context
from nose.tools import assert_equal
from test_api import TestAPI

from factories import UserFactory, CategoryFactory, ProjectFactory

from pybossa.repositories import ProjectRepository
from mock import MagicMock, patch

project_repo = ProjectRepository(db)


class TestCategoryAPI(TestAPI):

    @with_context
    def test_query_category(self):
        """Test API query for category endpoint works"""
        categories = []
        cat = CategoryFactory.create(name='thinking', short_name='thinking',
                                     info=dict(foo='monkey'))
        categories.append(cat.dictize())
        # Test for real field
        url = "/api/category"
        res = self.app.get(url + "?short_name=thinking")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'thinking', data

        # Valid field but wrong value
        res = self.app.get(url + "?short_name=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get(url + '?short_name=thinking&name=thinking')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'thinking', data
        assert data[0]['name'] == 'thinking', data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        for item in data:
            assert item['short_name'] == 'thinking', item
        assert len(data) == 1, data

        # Keyset pagination
        cat = CategoryFactory.create(name='computing', short_name='computing')
        categories.append(cat.dictize())
        res = self.app.get(url)
        data = json.loads(res.data)
        tmp = '?limit=1&last_id=%s' % data[0]['id']
        res = self.app.get(url + tmp)
        data_new = json.loads(res.data)
        assert len(data_new) == 1, data_new
        assert data_new[0]['id'] == data[1]['id']

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # Desc filter
        url = "/api/category?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = "/api/category?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        categories_by_id = sorted(categories, key=lambda x: x['id'], reverse=False)
        for i in range(len(categories)):
            assert categories_by_id[i]['id'] == data[i]['id']

        # Desc filter
        url = "/api/category?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        categories_by_id = sorted(categories, key=lambda x: x['id'], reverse=True)
        for i in range(len(categories)):
            assert categories_by_id[i]['id'] == data[i]['id']

        # fulltextsearch
        url = '/api/category?info=foo::monkey&fulltextsearch=1'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)


    @with_context
    def test_category_post(self):
        """Test API Category creation and auth"""
        admin = UserFactory.create()
        user = UserFactory.create()
        name = 'Category'
        category = dict(
            name=name,
            short_name='category',
            description='description')
        data = json.dumps(category)
        # no api-key
        url = '/api/category'
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 401, (err_msg, res.data)
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Unauthorized', err_msg

        # now a real user but not admin
        res = self.app.post(url + '?api_key=' + user.api_key, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

        # now as an admin
        res = self.app.post(url + '?api_key=' + admin.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = 'Admin should be able to create a Category'
        assert res.status_code == 200, err_msg
        cat = project_repo.get_category_by(short_name=category['short_name'])
        assert err['id'] == cat.id, err_msg
        assert err['name'] == category['name'], err_msg
        assert err['short_name'] == category['short_name'], err_msg
        assert err['description'] == category['description'], err_msg

        # test re-create should fail
        res = self.app.post(url + '?api_key=' + admin.api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "DBIntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', wrong=15)
        res = self.app.post(url + '?api_key=' + admin.api_key,
                            data=json.dumps(data))
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "TypeError", (err_msg, err)
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post(url + '?api_key=' + user.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "TypeError exception should be raised"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "TypeError", err_msg
        assert res.status_code == 415, err_msg

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put(url + '/%s' % cat.id,
                           data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not admin!
        url = '/api/category/%s?api_key=%s' % (cat.id, user.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update categories of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        # Now as an admin
        res = self.app.put('/api/category/%s?api_key=%s' % (cat.id, admin.api_key),
                           data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get_category(cat.id)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == cat.id, error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s' % (cat.id, admin.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With not JSON data
        datajson = data
        res = self.app.put('/api/category/%s?api_key=%s' % (cat.id, admin.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # With wrong args in the URL
        data = dict(
            name='Category3',
            short_name='category3',
            description='description3')

        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s&search=select1' % (cat.id, admin.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # With reserved keys
        data = dict(id='123')

        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s' % (cat.id, admin.api_key),
                           data=datajson)
        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload: id", error

        # test delete
        ## anonymous
        res = self.app.delete(url + '/%s' % cat.id, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        ### real user but not admin
        url = '/api/category/%s?api_key=%s' % (cat.id, user.api_key)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error

        # As admin
        url = '/api/category/%s?api_key=%s' % (cat.id, admin.api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete a category that does not exist
        url = '/api/category/5000?api_key=%s' % admin.api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        assert error['exception_cls'] == 'NotFound', error

        # delete a category that does not exist
        url = '/api/category/?api_key=%s' % admin.api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error

    @with_context
    @patch('pybossa.api.api_base.caching')
    def test_category_cache_post_is_refreshed(self, caching_mock):
        """Test API category cache is updated after POST."""
        clean_category_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_category_mock)
        owner = UserFactory.create()
        name = 'Category'
        category = dict(
            name=name,
            short_name='category',
            description='description')
        data = json.dumps(category)
        # no api-key
        url = '/api/category?api_key=%s' % owner.api_key
        res = self.app.post(url, data=data)
        cat = json.loads(res.data)
        clean_category_mock.assert_called, res.data
        assert cat['name'] == name
