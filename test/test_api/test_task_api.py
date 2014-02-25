import json
from base import model, Fixtures, db
from nose.tools import assert_equal
from test_api import HelperAPI



class TestTaskAPI(HelperAPI):

    def test_02_task_query(self):
        """ Test API Task query"""
        res = self.app.get('/api/task')
        tasks = json.loads(res.data)
        assert len(tasks) == 10, tasks
        task = tasks[0]
        assert task['info']['question'] == 'My random question', task

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_05_task_post(self):
        '''Test API Task creation and auth'''
        user = db.session.query(model.User)\
                 .filter_by(name=Fixtures.name)\
                 .one()
        app = db.session.query(model.App)\
                .filter_by(owner_id=user.id)\
                .one()
        data = dict(app_id=app.id, state='0', info='my task data')
        root_data = dict(app_id=app.id, state='0', info='my root task data')
        root_data = json.dumps(root_data)

        ########
        # POST #
        ########

        # anonymous user
        # no api-key
        res = self.app.post('/api/task', data=json.dumps(data))
        error_msg = 'Should not be allowed to create'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user but not allowed as not owner!
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key_2,
                            data=json.dumps(data))

        error_msg = 'Should not be able to post tasks for apps of others'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        # now a real user
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key,
                            data=json.dumps(data))
        assert res.data, res
        datajson = json.loads(res.data)
        out = db.session.query(model.Task)\
                .filter_by(id=datajson['id'])\
                .one()
        assert out, out
        assert_equal(out.info, 'my task data'), out
        assert_equal(out.app_id, app.id)
        id_ = out.id

        # now the root user
        res = self.app.post('/api/task?api_key=' + Fixtures.root_api_key,
                            data=root_data)
        assert res.data, res
        datajson = json.loads(res.data)
        out = db.session.query(model.Task)\
                .filter_by(id=datajson['id'])\
                .one()
        assert out, out
        assert_equal(out.info, 'my root task data'), out
        assert_equal(out.app_id, app.id)
        root_id_ = out.id

        # POST with not JSON data
        url = '/api/task?api_key=%s' % Fixtures.api_key
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post(url + '&foo=bar', data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        data['wrongfield'] = 13
        res = self.app.post(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        ##########
        # UPDATE #
        ##########
        data = {'state': '1'}
        datajson = json.dumps(data)
        root_data = {'state': '4'}
        root_datajson = json.dumps(root_data)

        ## anonymous
        res = self.app.put('/api/task/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Task).get(id_)
        assert_equal(out2.state, data['state'])
        assert out2.id == out['id'], out

        ### root
        res = self.app.put('/api/task/%s?api_key=%s' % (root_id_, Fixtures.root_api_key),
                           data=root_datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Task).get(root_id_)
        assert_equal(out2.state, root_data['state'])

        # PUT with not JSON data
        res = self.app.put(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        ##########
        # DELETE #
        ##########
        ## anonymous
        res = self.app.delete('/api/task/%s' % id_)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        #### real user
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # DELETE returns 204
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)
        assert res.data == '', res.data

        #### root user
        url = '/api/task/%s?api_key=%s' % (root_id_, Fixtures.root_api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                  .filter_by(app_id=app.id)\
                  .all()
        assert tasks, tasks

    def test_11_allow_anonymous_contributors(self):
        """Test API allow anonymous contributors works"""
        app = db.session.query(model.App).first()

        # All users are allowed to participate by default
        # As Anonymous user
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg

        # As registered user
        self.register()
        self.signin()
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg
        self.signout()

        # Now only allow authenticated users
        app.allow_anonymous_contributors = False
        db.session.add(app)
        db.session.commit()

        # As Anonymous user
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id should be null"
        print task
        assert task['app_id'] is None, err_msg
        err_msg = "There should be an error message"
        err = "This application does not allow anonymous contributors"
        assert task['info'].get('error') == err, err_msg
        err_msg = "There should not be a question"
        assert task['info'].get('question') is None, err_msg

        # As registered user
        res = self.signin()
        print res.data
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg
        self.signout()

