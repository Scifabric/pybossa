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
from nose.tools import assert_equal
from test_api import HelperAPI



class TestCategoryAPI(HelperAPI):

    def test_query_category(self):
        """Test API query for category endpoint works"""
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

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

    def test_04_category_post(self):
        """Test API Category creation and auth"""
        name = u'Category'
        category = dict(
            name=name,
            short_name='category',
            description=u'description')
        data = json.dumps(category)
        # no api-key
        url = '/api/category'
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 401, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Unauthorized', err_msg

        # now a real user but not admin
        res = self.app.post(url + '?api_key=' + Fixtures.api_key, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

        # now as an admin
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = 'Admin should be able to create a Category'
        assert res.status_code == 200, err_msg
        cat = db.session.query(model.Category)\
                .filter_by(short_name=category['short_name']).first()
        id_ = err['id']
        assert err['id'] == cat.id, err_msg
        assert err['name'] == category['name'], err_msg
        assert err['short_name'] == category['short_name'], err_msg
        assert err['description'] == category['description'], err_msg

        # test re-create should fail
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "IntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', wrong=15)
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "ValueError", err_msg
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post(url + '?api_key=' + Fixtures.api_key,
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
        res = self.app.put(url + '/%s' % id_,
                           data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not admin!
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        # Now as an admin
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
                           data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Category).get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With not JSON data
        datajson = data
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
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
            description=u'description3')

        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s&search=select1' % (id_, Fixtures.root_api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        ## anonymous
        res = self.app.delete(url + '/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        ### real user but not admin
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error

        # As admin
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete a category that does not exist
        url = '/api/category/5000?api_key=%s' % Fixtures.root_api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        assert error['exception_cls'] == 'NotFound', error

        # delete a category that does not exist
        url = '/api/category/?api_key=%s' % Fixtures.root_api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error
