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
from mock import patch
from base import web, model, Fixtures, db, redis_flushall
from nose.tools import assert_equal, assert_raises
from test_api import HelperAPI



class TestAppAPI(HelperAPI):

    def test_01_app_query(self):
        """ Test API App query"""
        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 1, data
        app = data[0]
        assert app['info']['total'] == 150, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test a non-existant ID
        res = self.app.get('/api/app/3434209')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err

    def test_query_app(self):
        """Test API query for app endpoint works"""
        # Test for real field
        res = self.app.get("/api/app?short_name=test-app")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data

        # Valid field but wrong value
        res = self.app.get("/api/app?short_name=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/app?short_name=test-app&name=My New App')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New App', data

        # Limits
        res = self.app.get("/api/taskrun?app_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_04_app_post(self):
        """Test API App creation and auth"""
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/app', data=data)
        assert_equal(res.status, '401 UNAUTHORIZED',
                     'Should not be allowed to create')
        # now a real user
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        db.session.remove()

        # now a real user with headers auth
        headers = [('Authorization', Fixtures.api_key)]
        new_app = dict(
            name=name + '2',
            short_name='xxxx-project2',
            description='description2',
            owner_id=1,
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        new_app = json.dumps(new_app)
        res = self.app.post('/api/app', headers=headers,
                            data=new_app)
        out = db.session.query(model.App).filter_by(name=name + '2').one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project2'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        db.session.remove()

        # test re-create should fail
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "IntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', link='hateoas', wrong=15)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "ValueError", err_msg
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
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
        res = self.app.put('/api/app/%s' % id_,
                           data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)

        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # With wrong id
        res = self.app.put('/api/app/5000?api_key=%s' % Fixtures.api_key,
                           data=datajson)
        assert_equal(res.status, '404 NOT FOUND', res.data)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'NotFound', error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With empty fields
        data.pop('algo')
        data['name'] = None
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err

        data['name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err

        data['name'] = 'something'
        data['short_name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err


        # With not JSON data
        datajson = data
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # With wrong args in the URL
        data = dict(
            name=name,
            short_name='xxxx-project',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')

        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s&search=select1' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        ## anonymous
        res = self.app.delete('/api/app/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error
        ### real user but not allowed as not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error

        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete an app that does not exist
        url = '/api/app/5000?api_key=%s' % Fixtures.api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error
        assert error['exception_cls'] == 'NotFound', error

        # delete an app that does not exist
        url = '/api/app/?api_key=%s' % Fixtures.api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error

    def test_04_admin_app_post(self):
        """Test API App update/delete for ADMIN users"""
        self.register()
        user = db.session.query(model.User).first()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            owner_id=user.id,
            description='description',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        datajson = json.dumps(data)
        # now a real user (we use the second api_key as first user is an admin)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=datajson)


        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester-2')
        id_ = out.id
        db.session.remove()

        # POST with not JSON data
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post('/api/app?api_key=%s&foo=bar' % Fixtures.api_key_2,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        data['wrongfield'] = 13
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ### admin user but not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        res = self.app.put(url, data=datajson)

        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

        # PUT with not JSON data
        res = self.app.put(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        # test delete
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        ### DELETE success real user  not owner!
        res = self.app.delete(url, data=json.dumps(data))
        assert_equal(res.status, '204 NO CONTENT', res.data)

    def test_07_user_progress_anonymous(self):
        """Test API userprogress as anonymous works"""
        self.signout()
        app = db.session.query(model.App).get(1)
        tasks = db.session.query(model.Task)\
                  .filter(model.Task.app_id == app.id)\
                  .all()

        # User ID = 2 because, the 1 is the root user
        taskruns = db.session.query(model.TaskRun)\
                     .filter(model.TaskRun.app_id == app.id)\
                     .filter(model.TaskRun.user_id == 2)\
                     .all()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)

        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], data

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)
        # Add a new TaskRun and check again
        tr = model.TaskRun(app_id=1, task_id=data['id'], user_id=1,
                           info={'answer': u'annakarenina'})
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    def test_08_user_progress_authenticated_user(self):
        """Test API userprogress as an authenticated user works"""
        self.register()
        self.signin()
        user = db.session.query(model.User)\
                 .filter(model.User.name == 'johndoe')\
                 .first()
        app = db.session.query(model.App)\
                .get(1)
        tasks = db.session.query(model.Task)\
                  .filter(model.Task.app_id == app.id)\
                  .all()

        taskruns = db.session.query(model.TaskRun)\
                     .filter(model.TaskRun.app_id == app.id)\
                     .filter(model.TaskRun.user_id == user.id)\
                     .all()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/app/%s/userprogress' % app.short_name
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/app/5000/userprogress'
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        url = '/api/app/userprogress'
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], error_msg

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)

        # Add a new TaskRun and check again
        tr = model.TaskRun(app_id=1, task_id=data['id'], user_id=user.id,
                           info={'answer': u'annakarenina'})
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg
        self.signout()
