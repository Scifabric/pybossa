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



class TestTaskrunAPI(HelperAPI):

    def test_query_taskrun(self):
        """Test API query for taskrun endpoint works"""
        # Test for real field
        res = self.app.get("/api/taskrun?app_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/taskrun?app_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/taskrun?app_id=1&task_id=1')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['app_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        # Limits
        res = self.app.get("/api/taskrun?app_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_03_taskrun_query(self):
        """Test API TaskRun query"""
        res = self.app.get('/api/taskrun')
        taskruns = json.loads(res.data)
        assert len(taskruns) == 10, taskruns
        taskrun = taskruns[0]
        assert taskrun['info']['answer'] == 'annakarenina', taskrun

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_06_taskrun_post(self):
        """Test API TaskRun creation and auth for anonymous users"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id

        # Create taskrun
        data = dict(
            app_id=app_id,
            task_id=task.id,
            info='my task result')

        datajson = json.dumps(data)

        # anonymous user

        # Get NotFound for an non-existing app
        url = '/api/app/5000/newtask'
        res = self.app.get(url)
        err = json.loads(res.data)
        err_msg = "The app does not exist"
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 404, err_msg
        assert err['exception_cls'] == 'NotFound', err_msg
        assert err['target'] == 'app', err_msg

        # Get an empty task
        url = '/api/app/%s/newtask?offset=1000' % app_id
        res = self.app.get(url)
        assert res.data == '{}', res.data

        # With wrong app_id
        data['app_id'] = 100000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = "This post should fail as the app_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, tmp.data
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid app_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['app_id'] = task.app_id
        data['task_id'] = 100000000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid task_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # Now with everything fine
        data = dict(
            app_id=task.app_id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun

        # If the anonymous tries again it should be forbidden
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = ("Anonymous users should be only allowed to post \
                    one task_run per task")
        assert tmp.status_code == 403, err_msg

    def test_06_taskrun_authenticated_post(self):
        """Test API TaskRun creation and auth for authenticated users"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id

        # Create taskrun
        data = dict(
            app_id=app_id,
            task_id=task.id,
            info='my task result')

        # With wrong app_id
        data['app_id'] = 100000000000000000
        datajson = json.dumps(data)
        url = '/api/taskrun?api_key=%s' % Fixtures.api_key
        tmp = self.app.post(url, data=datajson)
        err_msg = "This post should fail as the app_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid app_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['app_id'] = task.app_id
        data['task_id'] = 100000000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        err_msg = "This post should fail as the task_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid task_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # Now with everything fine
        data = dict(
            app_id=task.app_id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun

        # If the user tries again it should be forbidden
        tmp = self.app.post(url, data=datajson)
        err_msg = ("Authorized users should be only allowed to post \
                    one task_run per task")
        task_runs = self.app.get('/api/taskrun')
        assert tmp.status_code == 403, tmp.data

    def test_06_taskrun_post_with_bad_data(self):
        """Test API TaskRun error messages."""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        app_id = app.id
        task_run = dict(app_id=app_id, task_id=task.id, info='my task result')
        url = '/api/taskrun?api_key=%s' % Fixtures.api_key

        # POST with not JSON data
        res = self.app.post(url, data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post(url + '&foo=bar', data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        task_run['wrongfield'] = 13
        res = self.app.post(url, data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err
        task_run.pop('wrongfield')

    def test_06_taskrun_update(self):
        """Test TaskRun API update works."""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id
        task_run = dict(app_id=app_id, task_id=task.id, info='my task result')

        # Post a task_run
        url = '/api/taskrun'
        tmp = self.app.post(url, data=json.dumps(task_run))

        # Save task_run ID for anonymous user
        _id_anonymous = json.loads(tmp.data)['id']

        url = '/api/taskrun?api_key=%s' % Fixtures.api_key
        tmp = self.app.post(url, data=json.dumps(task_run))

        # Save task_run ID for real user
        _id = json.loads(tmp.data)['id']

        task_run['info'] = 'another result, I had a typo in the previous one'
        datajson = json.dumps(task_run)

        # anonymous user
        # No one can update anonymous TaskRuns
        url = '/api/taskrun/%s' % _id_anonymous
        res = self.app.put(url, data=datajson)
        taskrun = db.session.query(model.TaskRun)\
                    .filter_by(id=_id_anonymous)\
                    .one()
        assert taskrun, taskrun
        assert_equal(taskrun.user, None)
        error_msg = 'Should not be allowed to update'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user
        url = '/api/taskrun/%s' % _id
        out = self.app.get(url, follow_redirects=True)
        task = json.loads(out.data)
        datajson = json.loads(datajson)
        datajson['link'] = task['link']
        datajson['links'] = task['links']
        datajson = json.dumps(datajson)
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.TaskRun).get(_id)
        assert_equal(out2.info, task_run['info'])
        assert_equal(out2.user.name, Fixtures.name)
        assert out2.id == out['id'], out

        # PUT with not JSON data
        res = self.app.put(url, data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        task_run['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        task_run.pop('wrongfield')

        # root user
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.root_api_key)
        res = self.app.put(url, data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.TaskRun).get(_id)
        assert_equal(out2.info, task_run['info'])
        assert_equal(out2.user.name, Fixtures.name)

        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/taskrun/%s' % _id)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed to delete anonymous TaskRuns
        url = '/api/taskrun/%s?api_key=%s' % (_id_anonymous, Fixtures.api_key)
        res = self.app.delete(url)
        error_msg = 'Authenticated user should not be allowed ' \
                    'to delete anonymous TaskRuns'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2)
        res = self.app.delete(url)
        error_msg = 'Should not be able to delete TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key)
        res = self.app.delete(url + "&foo=bar", data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # Owner with valid args can delete
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                  .filter_by(app_id=app_id)\
                  .all()
        assert tasks, tasks

        ### root
        url = '/api/taskrun/%s?api_key=%s' % (_id_anonymous, Fixtures.root_api_key)
        res = self.app.delete(url)
        error_msg = 'Admin should be able to delete TaskRuns of others'
        assert_equal(res.status, '204 NO CONTENT', error_msg)

    def test_taskrun_newtask(self):
        """Test API App.new_task method and authentication"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # as a real user
        url = '/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key)
        res = self.app.get(url)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # test wit no TaskRun items in the db
        db.session.query(model.TaskRun).delete()
        db.session.commit()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # as a real user
        url = '/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key)
        res = self.app.get(url)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)
