import os
import random

import pybossa.web as web
import pybossa.model as model
from pybossa.core import db, mail, cache, app

_here = os.path.dirname(__file__)
web.app.config['TESTING'] = True
web.app.config['CSRF_ENABLED'] = False
web.app.config['SQLALCHEMY_DATABASE_URI'] = web.app.config['SQLALCHEMY_DATABASE_TEST_URI']
web.app.config['CSRF_ENABLED'] = False
web.app.config['MAIL_SERVER'] = 'localhost'
web.app.config['MAIL_USERNAME'] = None
web.app.config['MAIL_PASSWORD'] = None
web.app.config['MAIL_PORT'] = 25
web.app.config['MAIL_FAIL_SILENTLY'] = False
web.app.config['MAIL_DEFAULT_SENDER'] = 'PyBossa Support <info@pybossa.com>'

web.cache.config['CACHE_TYPE'] = 'null'
web.cache.config['TESTING'] = True
web.app.config['ANNOUNCEMENT'] = {'admin': 'Root Message',
                                  'user': 'User Message',
                                  'owner': 'Owner Message'}
cache.init_app(web.app)
mail.init_app(web.app)
#engine = model.create_engine(web.app.config['SQLALCHEMY_DATABASE_URI'])
#model.set_engine(engine)

class Fixtures:
    fullname = u'T Tester'
    fullname2 = u'T Tester 2'
    email_addr = u'tester@tester.com'
    email_addr2 = u'tester-2@tester.com'
    root_addr = u'root@root.com'
    name = u'tester'
    name2 = u'tester-2'
    root_name = u'root'
    api_key = 'tester'
    api_key_2 = 'tester-2'
    root_api_key = 'root'
    app_name = u'My New App'
    app_short_name = u'test-app'
    password = u'tester'

    @classmethod
    def create(cls,sched='default'):
        root, user,user2 = Fixtures.create_users()

        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        app = Fixtures.create_app(info)
        app.owner = user

        db.session.add(root)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        db.session.add(user2)
        db.session.commit()
        db.session.add(app)

        task_info = {
            'n_answers': 10,
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        for i in range (0,10):
             task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, app, user,i)
             db.session.add_all([task, task_run])
        db.session.commit()
        db.session.remove()

    @classmethod
    def create_2(cls,sched='default'):
        root, user,user2 = Fixtures.create_users()

        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        app = Fixtures.create_app(info)
        app.owner = user

        db.session.add_all([root, user, user2, app])

        task_info = {
            'n_answers': 10,
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, app, user,1)
        db.session.add_all([task, task_run])

        db.session.commit()
        db.session.remove()


    @classmethod
    def create_users(cls):
        root = model.User(
                email_addr = cls.root_addr,
                name = cls.root_name,
                passwd_hash = cls.password + 'root',
                fullname = cls.fullname,
                api_key = cls.root_api_key)
        root.set_password(cls.password + 'root')

        user = model.User(
                email_addr = cls.email_addr,
                name = cls.name,
                passwd_hash = cls.password,
                fullname = cls.fullname,
                api_key = cls.api_key)

        user.set_password(cls.password)

        user2 = model.User(
                email_addr = cls.email_addr2,
                name = cls.name2,
                passwd_hash = cls.password + "2",
                fullname = cls.fullname2,
                api_key=cls.api_key_2)

        user2.set_password(cls.password)

        return root, user, user2

    @classmethod
    def create_app(cls,info):
        app = model.App(
                name = cls.app_name,
                short_name = cls.app_short_name,
                description = u'description',
                hidden = 0,
                info = info
            )
        return app

    @classmethod
    def create_task_and_run(cls,task_info, task_run_info, app, user, order):
        task = model.Task(app_id = 1, state = '0', info = task_info, n_answers=10)
        task.app = app
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = model.TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = model.TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_ip = '127.0.0.%s' % order,
                    info = task_run_info)
        task_run.task = task
        return task,task_run


class webHelper:
    """Class to help testing the web interface"""

    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def html_title(self, title=None):
        """Helper function to create an HTML title"""
        if title is None:
            return "<title>PyBossa</title>"
        else:
            return "<title>PyBossa &middot; %s</title>" % title

    def register(self, method="POST", fullname="John Doe", username="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register',
                                 data={
                                     'fullname': fullname,
                                     'username': username,
                                     'email_addr': email,
                                     'password': password,
                                     'confirm': password2},
                                 follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next is not None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data={'email': email,
                                            'password': password},
                                 follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def profile(self):
        """Helper function to check profile of signed in user"""
        return self.app.get("/account/profile", follow_redirects=True)

    def update_profile(self, method="POST", id=1, fullname="John Doe",
                       name="johndoe", locale="es", email_addr="johndoe@example.com"):
        """Helper function to update the profile of users"""
        if (method == "POST"):
            return self.app.post("/account/profile/update",
                                 data={'id': id,
                                       'fullname': fullname,
                                       'name': name,
                                       'locale': locale,
                                       'email_addr': email_addr},
                                 follow_redirects=True)
        else:
            return self.app.get("/account/profile/update",
                                follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

    def new_application(self, method="POST", name="Sample App",
                        short_name="sampleapp", description="Description",
                        thumbnail='An Icon link',
                        allow_anonymous_contributors='True',
                        long_description=u'<div id="long_desc">Long desc</div>',
                        sched='default',
                        hidden=False):
        """Helper function to create an application"""
        if method == "POST":
            if hidden:
                return self.app.post("/app/new", data={
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'thumbnail': thumbnail,
                    'allow_anonymou_contributors': allow_anonymous_contributors,
                    'long_description': long_description,
                    'sched': sched,
                    'hidden': hidden,
                }, follow_redirects=True)
            else:
                return self.app.post("/app/new", data={
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'thumbnail': thumbnail,
                    'allow_anonymous_contributors': allow_anonymous_contributors,
                    'long_description': long_description,
                    'sched': sched,
                }, follow_redirects=True)
        else:
            return self.app.get("/app/new", follow_redirects=True)

    def new_task(self, appid):
        """Helper function to create tasks for an app"""
        tasks = []
        for i in range(0, 10):
            tasks.append(model.Task(app_id=appid, state='0', info={}))
        db.session.add_all(tasks)
        db.session.commit()

    def delTaskRuns(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(model.TaskRun).filter_by(app_id=1).delete()
        db.session.commit()

    def delete_application(self, method="POST", short_name="sampleapp"):
        """Helper function to create an application"""
        if method == "POST":
            return self.app.post("/app/%s/delete" % short_name,
                                 follow_redirects=True)
        else:
            return self.app.get("/app/%s/delete" % short_name,
                                follow_redirects=True)

    def update_application(self, method="POST", short_name="sampleapp", id=1,
                           new_name="Sample App", new_short_name="sampleapp",
                           new_description="Description",
                           new_thumbnail="New Icon link",
                           new_allow_anonymous_contributors="False",
                           new_long_description="Long desc",
                           new_sched="random",
                           new_hidden=False):
        """Helper function to create an application"""
        if method == "POST":
            if new_hidden:
                return self.app.post("/app/%s/update" % short_name,
                                     data={
                                         'id': id,
                                         'name': new_name,
                                         'short_name': new_short_name,
                                         'description': new_description,
                                         'thumbnail': new_thumbnail,
                                         'allow_anonymous_contributors': new_allow_anonymous_contributors,
                                         'long_description': new_long_description,
                                         'sched': new_sched,
                                         'hidden': new_hidden},
                                     follow_redirects=True)
            else:
                return self.app.post("/app/%s/update" % short_name,
                                     data={'id': id, 'name': new_name,
                                           'short_name': new_short_name,
                                           'thumbnail': new_thumbnail,
                                           'allow_anonymous_contributors': new_allow_anonymous_contributors,
                                           'long_description': new_long_description,
                                           'sched': new_sched,
                                           'description': new_description},
                                     follow_redirects=True)
        else:
            return self.app.get("/app/%s/update" % short_name,
                                follow_redirects=True)
