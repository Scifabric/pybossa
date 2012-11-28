import json
#import urllib

from flaskext.login import current_user

from base import web, model, Fixtures, db
from nose.tools import assert_equal


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()
        self.endpoints = ['app', 'task', 'taskrun']

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Helper functions
    def register(self, method="POST", fullname="John Doe", username="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register', data={
                'fullname': fullname,
                'username': username,
                'email_addr': email,
                'password': password,
                'confirm': password2,
                }, follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    def signin(self, method="POST", username="johndoe", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next != None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data={
                    'username': username,
                    'password': password,
                    }, follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

    def test_00_limits_query(self):
        """Test API GET limits works"""
        for i in range(30):
            app = model.App(name="name%s" % i,
                            short_name="short_name%s" % i,
                            description="desc",
                            owner_id=1)

            info = dict(a=0)
            task = model.Task(app_id=1, info=info)
            taskrun = model.TaskRun(app_id=1, task_id=1)
            db.session.add(app)
            db.session.add(task)
            db.session.add(taskrun)
        db.session.commit()

        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/app?limit=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        res = self.app.get('/api/app?limit=10&offset=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name')=='name9'

        res = self.app.get('/api/task')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/taskrun')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

    def test_01_app_query(self):
        """ Test API App query"""
        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 1, data
        app = data[0]
        assert app['info']['total'] == 150, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_get_query_with_api_key(self):
        """ Test API GET query with an API-KEY"""
        for endpoint in self.endpoints:
            res = self.app.get('/api/' + endpoint + '?api_key='\
                    + Fixtures.api_key)
            data = json.loads(res.data)

            if endpoint == 'app':
                assert len(data) == 1, data
                app = data[0]
                assert app['info']['total'] == 150, data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 10, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 10, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

    def test_query_search_wrongfield(self):
        """ Test API query search works"""
        # Test first a non-existant field for all end-points
        endpoints = ['app', 'task', 'taskrun']
        for endpoint in endpoints:
            res = self.app.get("/api/%s?wrongfield=value" % endpoint)
            data = json.loads(res.data)
            assert "no such column: wrongfield" in data['error'], data

    def test_query_sql_injection(self):
        """Test API SQL Injection is not allowed works"""

        q = '1%3D1;SELECT%20*%20FROM%20task%20WHERE%201=1'
        res = self.app.get('/api/task?' + q)
        data = json.loads(res.data)
        assert "no such column: " in data['error'], data
        q = 'app_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api/task?' + q)
        data = json.loads(res.data)
        assert "invalid input syntax" in data['error'], data


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
        assert data[0]['app_id'] == 1, data
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
        assert data[0]['app_id'] == 1, data
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
            short_name='xxxx-project',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/app',
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN',
                'Should not be allowed to create')
        # now a real user
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
            data=data,
        )
        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        db.session.remove()

        # test update
        data = {
            'name': 'My New Title'
            }
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put('/api/app/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN',
                'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.put('/api/app/%s?api_key=%s' %\
                (id_, Fixtures.api_key_2), data=datajson)
        assert_equal(res.status,\
                '401 UNAUTHORIZED',\
                'Should not be able to update apps of others')

        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

        # test delete
        ## anonymous
        res = self.app.delete('/api/app/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN',
                'Anonymous should not be allowed to delete')
        ### real user but not allowed as not owner!
        res = self.app.delete('/api/app/%s?api_key=%s' %
                (id_, Fixtures.api_key_2), data=datajson)
        assert_equal(res.status, '401 UNAUTHORIZED',
                'Should not be able to delete apps of others')

        res = self.app.delete('/api/app/%s?api_key=%s' %
                (id_, Fixtures.api_key), data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

    def test_04_admin_app_post(self):
        """Test API App update/delete for ADMIN users"""
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        data = json.dumps(data)
        # now a real user (we use the second api_key as first user is an admin)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
            data=data,
        )
        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester-2')
        id_ = out.id
        db.session.remove()

        # test update
        data = {
            'name': 'My New Title'
            }
        datajson = json.dumps(data)
        ### admin user but not owner!
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

        # test delete
        ### real user  not owner!
        res = self.app.delete('/api/app/%s?api_key=%s' %\
                (id_, Fixtures.api_key), data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)


    def test_05_task_post(self):
        '''Test API Task creation and auth'''
        user = db.session.query(model.User)\
                .filter_by(name=Fixtures.name)\
                .one()
        app = db.session.query(model.App)\
                .filter_by(owner_id=user.id)\
                .one()
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
        assert_equal(res.status, '403 FORBIDDEN',\
                'Should not be allowed to create')

        ### real user but not allowed as not owner!
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key_2,
            data=data
        )
        #print res.status
        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Should not be able to post tasks for apps of others')

        # now a real user
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key,
            data=data,
        )
        assert res.data, res
        datajson = json.loads(res.data)
        out = db.session.query(model.Task)\
                .filter_by(id=datajson['id'])\
                .one()
        assert out, out
        assert_equal(out.info, 'my task data'), out
        assert_equal(out.app_id, app.id)
        id_ = out.id

        ##########
        # UPDATE #
        ##########

        data = {
            'state': '1'
            }
        datajson = json.dumps(data)

        ## anonymous
        res = self.app.put('/api/task/%s' % id_,
            data=data
        )
        assert_equal(res.status, '403 FORBIDDEN',\
                'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.put('/api/task/%s?api_key=%s' %\
                (id_, Fixtures.api_key_2), data=datajson)
        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Should not be able to update tasks of others')

        ### real user
        res = self.app.put('/api/task/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Task).get(id_)
        assert_equal(out2.state, data['state'])

        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/task/%s' % id_)
        assert_equal(res.status, '403 FORBIDDEN',\
                'Anonymous should not be allowed to update')
        ### real user but not allowed as not owner!
        res = self.app.delete('/api/task/%s?api_key=%s' %\
                (id_, Fixtures.api_key_2))
        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Should not be able to update tasks of others')

        #### real user
        res = self.app.delete('/api/task/%s?api_key=%s' %\
                (id_, Fixtures.api_key))
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                .filter_by(app_id=app.id)\
                .all()
        assert tasks, tasks

    def test_06_taskrun_post(self):
        """Test API TaskRun creation and auth"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_name)\
                .one()
        tasks = db.session.query(model.Task)\
                .filter_by(app_id=app.id)

        app_id = app.id

        # Create taskrun
        data = dict(
            app_id=app_id,
            task_id=tasks[0].id,
            info='my task result'
            )

        datajson = json.dumps(data)

        # anonymous user
        # any user can create a TaskRun
        res = self.app.post('/api/taskrun',
                data=datajson)

        taskrun = db.session.query(model.TaskRun)\
                .filter_by(info=data['info'])\
                .one()
        _id_anonymous = taskrun.id
        assert taskrun, taskrun
        assert taskrun.created, taskrun
        assert_equal(taskrun.app_id, app_id), taskrun

        # create task run as authenticated user
        res = self.app.post('/api/taskrun?api_key=%s' % Fixtures.api_key,
            data=datajson
        )
        taskrun = db.session.query(model.TaskRun)\
                .filter_by(app_id=app_id)\
                .all()[-1]
        _id = taskrun.id
        assert taskrun.app_id == app_id, taskrun
        assert taskrun.user.name == Fixtures.name, taskrun

        ##########
        # UPDATE #
        ##########

        data['info'] = 'another result, I had a typo in the previous one'
        datajson = json.dumps(data)

        # anonymous user
        # No one can update anonymous TaskRuns
        res = self.app.put('/api/taskrun/%s' %\
                _id_anonymous, data=datajson)
        taskrun = db.session.query(model.TaskRun)\
                .filter_by(id=_id_anonymous)\
                .one()
        assert taskrun, taskrun
        assert_equal(taskrun.user, None)
        assert_equal(res.status, '403 FORBIDDEN',\
                'Should not be allowed to update')
        # real user but not allowed as not owner!
        res = self.app.put('/api/taskrun/%s?api_key=%s' %\
                (_id, Fixtures.api_key_2), data=datajson)

        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Should not be able to update TaskRuns of others')

        # real user

        res = self.app.put('/api/taskrun/%s?api_key=%s' %\
                (_id, Fixtures.api_key), data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.TaskRun).get(_id)
        assert_equal(out2.info, data['info'])
        assert_equal(out2.user.name, Fixtures.name)

        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/taskrun/%s' % _id)
        assert_equal(res.status, '403 FORBIDDEN',\
                'Anonymous should not be allowed to delete')

        ### real user but not allowed to delete anonymous TaskRuns
        res = self.app.delete('/api/taskrun/%s?api_key=%s' %\
                (_id_anonymous, Fixtures.api_key))
        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Anonymous should not be allowed to delete anonymous TaskRuns')

        ### real user but not allowed as not owner!
        res = self.app.delete('/api/taskrun/%s?api_key=%s' %\
                (_id, Fixtures.api_key_2))
        assert_equal(res.status, '401 UNAUTHORIZED',\
                'Should not be able to delete TaskRuns of others')

        #### real user
        res = self.app.delete('/api/taskrun/%s?api_key=%s' %\
                (_id, Fixtures.api_key))
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                .filter_by(app_id=app_id)\
                .all()
        assert tasks, tasks

    def test_taskrun_newtask(self):
        """Test API App.new_task method and authentication"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_name)\
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
        res = self.app.get('/api/app/%s/newtask?api_key=%s' %\
                (app.id, Fixtures.api_key))
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
        res = self.app.get('/api/app/%s/newtask?api_key=%s' %\
                (app.id, Fixtures.api_key))
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

    def test_07_user_progress_anonymous(self):
        """Test API userprogress as anonymous works"""
        self.signout()
        app = db.session.query(model.App)\
                .get(1)
        tasks = db.session.query(model.Task)\
                .filter(model.Task.app_id == app.id)\
                .all()

        taskruns = db.session.query(model.TaskRun)\
                .filter(model.TaskRun.app_id == app.id)\
                .filter(model.TaskRun.user_id == 1)\
                .all()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        assert len(tasks) == data['total'],\
                "The reported total number of tasks is wrong"
        assert len(taskruns) == data['done'],\
                "The reported number of done tasks is wrong"

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)
        print data
        # Add a new TaskRun and check again
        tr = model.TaskRun(
                app_id=1,
                task_id=data['id'],
                user_id=1,
                info={'answer': u'annakarenina'}
                )
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        assert len(tasks) == data['total'],\
                "The reported total number of tasks is wrong"
        assert len(taskruns) + 1 == data['done'],\
                "The reported number of done tasks is wrong: %s" %\
                len(taskruns)

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
        assert len(tasks) == data['total'],\
                "The reported total number of tasks is wrong"
        assert len(taskruns) == data['done'],\
                "The reported number of done tasks is wrong"

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)
        print data
        # Add a new TaskRun and check again
        tr = model.TaskRun(
                app_id=1,
                task_id=data['id'],
                user_id=user.id,
                info={'answer': u'annakarenina'}
                )
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        assert len(tasks) == data['total'],\
                "The reported total number of tasks is wrong"
        assert len(taskruns) + 1 == data['done'],\
                "The reported number of done tasks is wrong: %s" %\
                len(taskruns)
        self.signout()
