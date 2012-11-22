import json
import urllib
import flask
import random

#from flaskext.login import login_user, logout_user, current_user

from base import web, model, Fixtures, db
from pybossa import sched

from nose.tools import assert_equal


class TestSCHED:
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

    def isTask(self, task_id, tasks):
        """Returns True if the task_id is in tasks list"""
        for t in tasks:
            if t.id==task_id:
                return True
        return False

    def isUnique(self,id,items):
        """Returns True if the id is not Unique"""
        copies = 0
        for i in items:
            if type(i) is dict:
                if i['id'] == id:
                    copies = copies + 1
            else:
                if i.id == id:
                    copies = copies + 1
        if copies>=2:
            return False
        else:
            return True

    def delTaskRuns(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(model.TaskRun).filter_by(app_id=1).delete()
        db.session.commit()
        db.session.remove()

    def register(self, method="POST", fullname="John Doe", username="johndoe", password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register', data = {
                'fullname': fullname,
                'username': username,
                'email_addr': email,
                'password': password,
                'confirm': password2,
                }, follow_redirects = True)
        else:
            return self.app.get('/account/register', follow_redirects = True)

    def signin(self, method="POST", username="johndoe", password="p4ssw0rd", next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next != None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data =  {
                    'username': username,
                    'password': password,
                    }, follow_redirects = True)
        else:
            return self.app.get(url, follow_redirects = True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects = True)


    def test_anonymous_01_newtask(self):
        """ Test SCHED newtask returns a Task for the Anonymous User"""
        # Del previous TaskRuns
        self.delTaskRuns()

        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        print data
        assert data['info'], data


    def test_anonymous_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for the Anonymous User"""
        # Del previous TaskRuns
        self.delTaskRuns()


        assigned_tasks = []
        # Get a Task until scheduler returns None
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        count = 0
        while (data.get('info')!=None and count < 10):
            count += 1
            # Check that we have received a Task
            assert data.get('info'),  data

            # Save the assigned task
            assigned_tasks.append(data)

            # Submit an Answer for the assigned task
            tr = model.TaskRun(app_id=data['app_id'], task_id=data['id'], 
                               user_ip="127.0.0.1",
                               info={'answer': 'Yes'})
            db.session.add(tr)
            db.session.commit()
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        for at in assigned_tasks:
            assert self.isTask(at['id'],tasks), "Assigned Task not found in DB Tasks"
        # Check that there are no duplicated tasks
        for at in assigned_tasks:
            assert self.isUnique(at['id'],assigned_tasks), "One Assigned Task is duplicated"

    def test_user_01_newtask(self):
        """ Test SCHED newtask returns a Task for John Doe User"""
        # Del previous TaskRuns
        self.delTaskRuns()

        # Register
        self.register()
        self.signin()
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        assert data['info'], data
        self.signout()

    def test_user_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for John Doe User"""
        # Del previous TaskRuns
        self.delTaskRuns()

        # Register
        self.register()
        self.signin()

        assigned_tasks = []
        # Get Task until scheduler returns None
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        while (data.get('info')!=None):
            # Check that we received a Task
            assert data.get('info'),  data

            # Save the assigned task
            assigned_tasks.append(data)

            # Submit an Answer for the assigned task
            tr = dict(
                    app_id = data['app_id'],
                    task_id = data['id'],
                    info = {'answer': 'No'}
                    )
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        assert len(assigned_tasks) == len(tasks), assigned_tasks
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        for at in assigned_tasks:
            assert self.isTask(at['id'],tasks), "Assigned Task not found in DB Tasks"
        # Check that there are no duplicated tasks
        for at in assigned_tasks:
            assert self.isUnique(at['id'],assigned_tasks), "One Assigned Task is duplicated"

    def test_get_default_task_anonymous(self):
        self._test_get_default_task()

    def test_get_default_task_user(self):
        user = Fixtures.create_users()[0]
        self._test_get_default_task(user)

    def _test_get_default_task(self, user=None):
        self.delTaskRuns()
        app = model.App(short_name='xyz')
        task = model.Task(app=app, state = '0', info={})
        task2 = model.Task(app=app, state = '0', info={})
        db.session.add(app)
        db.session.add(task)
        db.session.add(task2)
        db.session.commit()
        taskid = task.id
        appid = app.id
        # give task2 a bunch of runs
        for idx in range(2):
            self._add_task_run(task2)

        # now check we get task without task runs
        out = sched.get_default_task(appid)
        assert out.id == taskid, out

        self._add_task_run(task)
        out = sched.get_default_task(appid)
        assert out.id == taskid, out

        # now add 2 more taskruns. We now have 3 and 2 task runs per task
        self._add_task_run(task)
        self._add_task_run(task)
        out = sched.get_default_task(appid)
        assert out.id == task2.id, out

    def _add_task_run(self, task, user=None):
        tr = model.TaskRun(task=task, user=user)
        db.session.add(tr)
        db.session.commit()

