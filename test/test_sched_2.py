import json
import urllib
import flask
import random

#from flaskext.login import login_user, logout_user, current_user

from base import web, model, Fixtures, db
from nose.tools import assert_equal


class TestSCHED:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        self.endpoints = ['app', 'task', 'taskrun']

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


    def test_incremental_tasks(self):
        """ Test incremental SCHED strategy - second TaskRun receives first gaven answer"""

        Fixtures.create_2(sched='incremental')
        
        # Del previous TaskRuns
        self.delTaskRuns()

        # Register
        self.register(fullname="John Doe", username="johndoe", password="p4ssw0rd")
        self.register(fullname="Marie Doe", username="mariedoe", password="dr0wss4p")
        self.signin()

        # Get the only task with no runs!
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        # Check that we received a clean Task
        assert data.get('info'), data
        assert not data.get('info').get('last_answer')

        # Submit an Answer for the assigned task
        tr = dict(
            app_id = data['app_id'],
            task_id = data['id'],
            info = {'answer': 'No'}
            )
        tr = json.dumps(tr)

        self.app.post('/api/taskrun', data=tr)
        # No more tasks available for this user!
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        assert not data

        
        #### Get the only task now with an answer as Anonimous!
	self.signout()
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        
        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No'

        # Submit a second Answer as Anonimous
        tr = dict(
            app_id = data['app_id'],
            task_id = data['id'],
            info = {'answer': 'No No'}
            )
        tr = json.dumps(tr)

        self.app.post('/api/taskrun', data=tr)
 

        #### Get the only task now with an answer as User2!
	self.signin(username="mariedoe", password="dr0wss4p")
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        
        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No No'


