import json
import urllib

from flaskext.login import login_user, logout_user, current_user

from base import web, model, Fixtures
from nose.tools import assert_equal


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def test_01_app_query(self):
        """ Test API App query"""
        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 1, data
        app = data[0]
        assert app['info']['total'] == 150, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_query_search_wrongfield(self):
        """ Test API query search works"""
        # Test first a non-existant field for all end-points
        endpoints = ['app', 'task', 'taskrun']
        for endpoint in endpoints:
            res = self.app.get("/api/%s?wrongfield=value" % endpoint)
            data = json.loads(res.data)
            assert "no such column: wrongfield" in data['error']

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
        print res.data
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_query_task(self):
        """Test API query for task endpoint works"""
        # Test for real field
        res = self.app.get("/api/task?app_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/task?app_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/task?app_id=1&state=0')
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1 , data
        assert data[0]['state'] == '0', data

        # Limits
        res = self.app.get("/api/task?app_id=1&limit=5")
        print res.data
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

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
        assert data[0]['app_id'] == 1 , data
        assert data[0]['task_id'] == 1, data

        # Limits
        res = self.app.get("/api/taskrun?app_id=1&limit=5")
        print res.data
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data
    
    def test_02_task_query(self):
        """ Test API Task query"""
        res = self.app.get('/api/task')
        tasks = json.loads(res.data)
        assert len(tasks) == 10, tasks
        task = tasks[0]
        assert task['info']['question'] == 'My random question', task

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res


    def test_03_taskrun_query(self):
        """Test API TaskRun query"""
        res = self.app.get('/api/taskrun')
        taskruns = json.loads(res.data)
        assert len(taskruns) == 10, taskruns
        taskrun = taskruns[0]
        #print taskrun
        assert taskrun['info']['answer'] == 'annakarenina', taskrun

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_04_app_post(self):
        """Test API App creation and auth"""
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project'
            )
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/app',
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN', 'Should not be allowed to create')
        # now a real user
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
            data=data,
        )
        out = model.Session.query(model.App).filter_by(name=name).one()
        assert out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        model.Session.remove()

        # test update
        data = {
            'name': 'My New Title'
            }
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put('/api/app/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN', 'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2),
            data=datajson
        )
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to update apps of others')

        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '200 OK', res.data)
        out2 = model.Session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

        # test delete
        ## anonymous
        res = self.app.delete('/api/app/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN', 'Anonymous should not be allowed to delete')
        ### real user but not allowed as not owner!
        res = self.app.delete('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2),
            data=datajson
        )
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to delete apps of others')

        res = self.app.delete('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '204 NO CONTENT', res.data)

    def test_05_task_post(self):
        '''Test API Task creation and auth'''
        user = model.Session.query(model.User).filter_by(name = Fixtures.username).one()
        app = model.Session.query(model.App).filter_by(owner_id = user.id).one()
        data = dict(
            app_id=app.id,
            state='0',
            info='my task data'
            )
        data = json.dumps(data)

        ########
        # POST #
        ########

        # anonymous user
        # no api-key
        res = self.app.post('/api/task',
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN', 'Should not be allowed to create')

        ### real user but not allowed as not owner!
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key_2,
            data=data
        )
        #print res.status
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to post tasks for apps of others')

        # now a real user
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key,
            data=data,
        )
        assert res.data
        datajson = json.loads(res.data)
        out = model.Session.query(model.Task).filter_by(id=datajson['id']).one()
        assert out
        assert_equal(out.info, 'my task data'), out
        assert_equal(out.app_id, app.id)
        id_ = out.id

        ##########
        # UPDATE #
        ##########

        data = {
            'state':'1'
            }
        datajson = json.dumps(data)

        ## anonymous
        res = self.app.put('/api/task/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN', 'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.put('/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2),
            data=datajson
        )
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to update tasks of others')

        ### real user
        res = self.app.put('/api/task/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '200 OK', res.data)
        out2 = model.Session.query(model.Task).get(id_)
        assert_equal(out2.state, data['state'])


        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/task/%s' % id_)
        assert_equal(res.status, '403 FORBIDDEN', 'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.delete('/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2))
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to update tasks of others')

        #### real user
        res = self.app.delete('/api/task/%s?api_key=%s' % (id_, Fixtures.api_key))
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = model.Session.query(model.Task).filter_by(app_id=app.id).all()
        assert tasks, tasks

    def test_06_taskrun_post(self):
        """Test API TaskRun creation and auth"""
        # user = model.Session.query(model.User).filter_by(name = Fixtures.username).one()
        app = model.Session.query(model.App).filter_by(short_name = Fixtures.app_name ).one()
        tasks = model.Session.query(model.Task).filter_by(app_id = app.id)
    
        # Create taskrun
        data = dict(
            app_id=app.id,
            task_id=tasks[0].id,
            info='my task result'
            )
        datajson = json.dumps(data)
    
        # anonymous user
        # any user can create a TaskRun
        res = self.app.post('/api/taskrun',
            data=datajson
        )

        taskrun = model.Session.query(model.TaskRun).filter_by(info = data['info']).one()
        _id_anonymous = taskrun.id
        assert taskrun, taskrun
        assert taskrun.created, taskrun
        assert taskrun.app_id == app.id
    
        # create task run as authenticated user
        res = self.app.post('/api/taskrun?api_key=%s' % Fixtures.api_key,
            data=datajson
        )
        taskrun = model.Session.query(model.TaskRun).filter_by(app_id = app.id).all()[-1]
        _id = taskrun.id
        assert taskrun.app_id == app.id
        assert taskrun.user.name == Fixtures.username

        ##########
        # UPDATE #
        ##########

        data['info']= 'another result, I had a typo in the previous one'
        datajson = json.dumps(data)

        # anonymous user
        # No one can update anonymous TaskRuns
        res = self.app.put('/api/taskrun/%s' % _id_anonymous, data = datajson)
        taskrun = model.Session.query(model.TaskRun).filter_by(id = _id_anonymous).one()
        assert taskrun, taskrun
        assert_equal (taskrun.user, None)
        assert_equal(res.status, '403 FORBIDDEN', 'Should not be allowed to update')
        # real user but not allowed as not owner!
        res = self.app.put('/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2), data = datajson)

        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to update TaskRuns of others')

        # real user

        res = self.app.put('/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key), data = datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = model.Session.query(model.TaskRun).get(_id)
        assert_equal(out2.info,data['info'])
        assert_equal(out2.user.name, Fixtures.username)

        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/taskrun/%s' % _id)
        assert_equal(res.status, '403 FORBIDDEN', 'Anonymous should not be allowed to delete')

        ### real user but not allowed to delete anonymous TaskRuns
        res = self.app.delete('/api/taskrun/%s?api_key=%s' % (_id_anonymous, Fixtures.api_key))
        assert_equal(res.status, '401 UNAUTHORIZED', 'Anonymous should not be allowed to delete anonymous TaskRuns')

        ### real user but not allowed as not owner!
        res = self.app.delete('/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2))
        assert_equal(res.status, '401 UNAUTHORIZED', 'Should not be able to delete TaskRuns of others')

        #### real user
        res = self.app.delete('/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key))
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = model.Session.query(model.Task).filter_by(app_id=app.id).all()
        assert tasks, tasks


    def test_taskrun_newtask(self):
        """Test API App.new_task method and authentication"""
        app = model.Session.query(model.App).filter_by(short_name = Fixtures.app_name ).one()
        tasks = model.Session.query(model.Task).filter_by(app_id = app.id)

        
        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res


        # as a real user
        res = self.app.get('/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key))
        assert res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # test wit no TaskRun items in the db
        model.Session.query(model.TaskRun).delete()
        model.Session.commit()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # as a real user
        res = self.app.get('/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key))
        assert res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

