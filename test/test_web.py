import json
import csv
import StringIO

from base import web, model, Fixtures, mail
from mock import patch
from itsdangerous import BadSignature
from collections import namedtuple
from pybossa.core import db, signer
from pybossa.util import unicode_csv_reader
from pybossa.util import get_user_signup_method

FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestWeb:

    def setUp(self):
        self.app = web.app.test_client()
        #self.app.cache = web.cache.config['CACHE_TYPE']='nothingThatWillWork'
        model.rebuild_db()
        #Fixtures.create()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Helper functions
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
                return self.app.post("/app/%s/update" % short_name, data={
                        'id': id,
                        'name': new_name,
                        'short_name': new_short_name,
                        'thumbnail': new_thumbnail,
                        'allow_anonymous_contributors': new_allow_anonymous_contributors,
                        'long_description': new_long_description,
                        'sched': new_sched,
                        'description': new_description,
                    }, follow_redirects=True)
        else:
            return self.app.get("/app/%s/update" % short_name,
                                follow_redirects=True)

    # Tests

    def test_01_index(self):
        """Test WEB home page works"""
        res = self.app.get("/", follow_redirects=True)
        assert self.html_title() in res.data, res
        assert "Create an App" in res.data, res

    def test_02_stats(self):
        """Test WEB leaderboard or stats page works"""
        self.register()
        self.new_application()

        app = db.session.query(model.App).first()
        # We use a string here to check that it works too
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     user_id=1,
                                     info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        self.signout()

        res = self.app.get('/leaderboard', follow_redirects=True)
        assert self.html_title("Community Leaderboard") in res.data, res
        assert "John Doe" in res.data, res.data

    def test_03_register(self):
        """Test WEB register user works"""
        res = self.app.get('/account/signin')
        assert 'Forgot Password' in res.data

        res = self.register(method="GET")
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert self.html_title("Register") in res.data, res

        res = self.register()
        assert self.html_title() in res.data, res
        assert "Thanks for signing-up" in res.data, res.data

        res = self.register()
        assert self.html_title("Register") in res.data, res
        assert "The user name is already taken" in res.data, res

        res = self.register(fullname='')
        assert self.html_title("Register") in res.data, res
        assert "Full name must be between 3 and 35 characters long"\
                in res.data, res

        res = self.register(username='')
        assert self.html_title("Register") in res.data, res
        assert "User name must be between 3 and 35 characters long"\
                in res.data, res

        res = self.register(email='')
        assert self.html_title("Register") in res.data, res
        assert self.html_title("Register") in res.data, res
        assert "Email must be between 3 and 35 characters long"\
                in res.data, res

        res = self.register(email='invalidemailaddress')
        assert self.html_title("Register") in res.data, res
        assert "Invalid email address" in res.data, res

        res = self.register()
        assert self.html_title("Register") in res.data, res
        assert "Email is already taken" in res.data, res

        res = self.register(password='')
        assert self.html_title("Register") in res.data, res
        assert "Password cannot be empty" in res.data, res

        res = self.register(password2='different')
        assert self.html_title("Register") in res.data, res
        assert "Passwords must match" in res.data, res

    def test_04_signin_signout(self):
        """Test WEB sign in and sign out works"""
        res = self.register()
        # Log out as the registration already logs in the user
        res = self.signout()

        res = self.signin(method="GET")
        assert self.html_title("Sign in") in res.data, res.data
        assert "Sign in" in res.data, res.data

        res = self.signin(email='')
        assert "Please correct the errors" in  res.data, res
        assert "The e-mail is required" in res.data, res

        res = self.signin(password='')
        assert "Please correct the errors" in  res.data, res
        assert "You must provide a password" in res.data, res

        res = self.signin(email='', password='')
        assert "Please correct the errors" in  res.data, res
        assert "The e-mail is required" in res.data, res
        assert "You must provide a password" in res.data, res

        # Non-existant user
        msg = "Ooops, we didn't find you in the system"
        res = self.signin(email='wrongemail')
        assert msg in  res.data, res.data

        res = self.signin(email='wrongemail', password='wrongpassword')
        assert msg in  res.data, res

        # Real user but wrong password or username
        msg = "Ooops, Incorrect email/password"
        res = self.signin(password='wrongpassword')
        print res.data
        assert msg in  res.data, res

        res = self.signin()
        assert self.html_title() in res.data, res
        assert "Welcome back John Doe" in res.data, res

        # Check profile page with several information chunks
        res = self.profile()
        assert self.html_title("Profile") in res.data, res
        assert "John Doe" in res.data, res
        assert "johndoe@example.com" in res.data, res

        # Log out
        res = self.signout()
        assert self.html_title() in res.data, res
        assert "You are now signed out" in res.data, res

        # Request profile as an anonymous user
        res = self.profile()
        # As a user must be signed in to access, the page the title will be the
        # redirection to log in
        assert self.html_title("Sign in") in res.data, res
        assert "Please sign in to access this page." in res.data, res

        res = self.signin(next='%2Faccount%2Fprofile')
        assert self.html_title("Profile") in res.data, res
        assert "Welcome back John Doe" in res.data, res

    def test_05_update_user_profile(self):
        """Test WEB update user profile"""

        # Create an account and log in
        self.register()

        # Update profile with new data
        res = self.update_profile(method="GET")
        assert self.html_title("Update your profile: John Doe")\
                in res.data, res
        assert 'input id="id" name="id" type="hidden" value="1"'\
                in res.data, res
        assert "John Doe" in res.data, res
        assert "Save the changes" in res.data, res
        assert '<a href="/account/profile/settings" class="btn">Cancel</a>' in \
                res.data, res

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en")
        assert self.html_title("Profile") in res.data, res.data
        assert "Your profile has been updated!" in res.data, res.data
        assert "John Doe 2" in res.data, res
        assert "johndoe" in res.data, res
        assert "johndoe2@example.com" in res.data, res

        # Updating the username field forces the user to re-log in
        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en",
                                  name="johndoe2")
        assert "Your profile has been updated!" in res.data, res
        assert "Please sign in to access this page" in res.data, res

        res = self.signin(method="POST", email="johndoe2@example.com",
                          password="p4ssw0rd",
                          next="%2Faccount%2Fprofile")
        assert "Welcome back John Doe 2" in res.data, res.data
        assert "John Doe 2" in res.data, res
        assert "johndoe2" in res.data, res
        assert "johndoe2@example.com" in res.data, res

        res = self.signout()
        assert self.html_title() in res.data, res
        assert "You are now signed out" in res.data, res

        # A user must be signed in to access the update page, the page
        # the title will be the redirection to log in
        res = self.update_profile(method="GET")
        assert self.html_title("Sign in") in res.data, res
        assert "Please sign in to access this page." in res.data, res

        # A user must be signed in to access the update page, the page
        # the title will be the redirection to log in
        res = self.update_profile()
        assert self.html_title("Sign in") in res.data, res
        assert "Please sign in to access this page." in res.data, res

    def test_05a_get_nonexistant_app(self):
        """Test WEB get not existant app should return 404"""
        res = self.app.get('/app/nonapp', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_05b_get_nonexistant_app_newtask(self):
        """Test WEB get non existant app newtask should return 404"""
        res = self.app.get('/app/noapp/presenter', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        res = self.app.get('/app/noapp/newtask', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_05c_get_nonexistant_app_tutorial(self):
        """Test WEB get non existant app tutorial should return 404"""
        res = self.app.get('/app/noapp/tutorial', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_05d_get_nonexistant_app_delete(self):
        """Test WEB get non existant app delete should return 404"""
        self.register()
        # GET
        res = self.app.get('/app/noapp/delete', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.data
        # POST
        res = self.delete_application(short_name="noapp")
        assert res.status == '404 NOT FOUND', res.status

    def test_05d_get_nonexistant_app_update(self):
        """Test WEB get non existant app update should return 404"""
        self.register()
        # GET
        res = self.app.get('/app/noapp/update', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # POST
        res = self.update_application(short_name="noapp")
        assert res.status == '404 NOT FOUND', res.status

    def test_05d_get_nonexistant_app_import(self):
        """Test WEB get non existant app import should return 404"""
        self.register()
        # GET
        res = self.app.get('/app/noapp/import', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # POST
        res = self.app.post('/app/noapp/import', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_05d_get_nonexistant_app_task(self):
        """Test WEB get non existant app task should return 404"""
        res = self.app.get('/app/noapp/task', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Pagination
        res = self.app.get('/app/noapp/task/25', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_05d_get_nonexistant_app_results_json(self):
        """Test WEB get non existant app results json should return 404"""
        res = self.app.get('/app/noapp/24/results.json', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    def test_06_applications(self):
        """Test WEB applications index interface works"""
        # Check first without apps
        res = self.app.get('/app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured" in res.data, res.data
        assert "Published" in res.data, res.data
        assert "Draft" in res.data, res.data

        Fixtures.create()

        res = self.app.get('/app', follow_redirects=True)
        assert self.html_title("Applications") in res.data, res.data
        assert "Applications" in res.data, res.data
        assert '/app/test-app' in res.data, res.data

    def test_06_featured_apps(self):
        """Test WEB application index shows featured apps in all the pages works"""
        Fixtures.create()

        f = model.Featured()
        f.app_id=1
        db.session.add(f)
        db.session.commit()

        res = self.app.get('/app', follow_redirects=True)
        assert self.html_title("Applications") in res.data, res.data
        assert "Applications" in res.data, res.data
        assert '/app/test-app' in res.data, res.data
        assert '<h2><a href="/app/test-app/">My New App</a></h2>' in res.data, res.data

    def test_10_get_application(self):
        """Test WEB application URL/<short_name> works"""
        # Sign in and create an application
        self.register()
        res = self.new_application()

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App")\
                in res.data, res
        err_msg = "There should be a contribute button"
        assert "Start Contributing Now" in res.data, err_msg

        res = self.app.get('/app/sampleapp/settings', follow_redirects=True)
        assert res.status == '200 OK', res.status
        self.signout()

        # Now as an anonymous user
        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Start Contributing Now" in res.data, err_msg
        res = self.app.get('/app/sampleapp/settings', follow_redirects=True)
        assert res.status == '200 OK', res.status
        err_msg = "Anonymous user should be redirected to sign in page"
        assert "Please sign in to access this page" in res.data, err_msg

        # Now with a different user
        self.register(fullname="Perico Palotes", username="perico")
        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Start Contributing Now" in res.data, err_msg
        res = self.app.get('/app/sampleapp/settings')
        assert res.status == '403 FORBIDDEN', res.status

    def test_11_create_application(self):
        """Test WEB create an application works"""
        # Create an app as an anonymous user
        res = self.new_application(method="GET")
        assert self.html_title("Sign in") in res.data, res
        assert "Please sign in to access this page" in res.data, res

        res = self.new_application()
        assert self.html_title("Sign in") in res.data, res.data
        assert "Please sign in to access this page." in res.data, res.data

        # Sign in and create an application
        res = self.register()

        res = self.new_application(method="GET")
        assert self.html_title("Create an Application") in res.data, res
        assert "Create the application" in res.data, res

        res = self.new_application()
        assert "<strong>Sample App</strong>: Settings" in res.data, res
        assert "Application created!" in res.data, res

        app = db.session.query(model.App).first()
        assert app.name == 'Sample App', 'Different names %s' % app.name
        assert app.short_name == 'sampleapp', \
            'Different names %s' % app.short_name
        assert app.info['thumbnail'] == 'An Icon link', \
            "Thumbnail should be the same: %s" % app.info['thumbnail']
        assert app.info['sched'] == 'default', \
            "Scheduler should be the same: %s" % app.info['thumbnail']
        assert app.long_description == '<div id="long_desc">Long desc</div>', \
            "Long desc should be the same: %s" % app.long_description

    def test_12_update_application(self):
        """Test WEB update application works"""
        self.register()
        self.new_application()

        # Get the Update App web page
        res = self.update_application(method="GET")
        assert self.html_title("Application: Sample App &middot; Update")\
                in res.data, res
        assert 'input id="id" name="id" type="hidden" value="1"'\
                in res.data, res
        assert "Save the changes" in res.data, res

        # Update the application
        res = self.update_application(new_name="New Sample App",
                                      new_short_name="newshortname",
                                      new_description="New description",
                                      new_thumbnail="New Icon Link",
                                      new_long_description='New long desc',
                                      new_sched="random",
                                      new_hidden=True)
        app = db.session.query(model.App).first()
        assert "Application updated!" in res.data, res
        assert app.name == "New Sample App", \
                "App name not updated %s" % app.name
        assert app.short_name == "newshortname", \
                "App short name not updated %s" % app.short_name
        assert app.description == "New description", \
                "App description not updated %s" % app.description
        assert app.info['thumbnail'] == "New Icon Link", \
                "App thumbnail not updated %s" % app.icon['thumbnail']
        assert app.long_description == "New long desc", \
                "App long description not updated %s" % app.long_description
        assert app.hidden == True, \
                "App hidden not updated %s" % app.hidden

    def test_13_hidden_applications(self):
        """Test WEB hidden application works"""
        self.register()
        self.new_application()
        self.update_application(new_hidden=True)
        self.signout()

        res = self.app.get('/app/', follow_redirects=True)
        assert "Sample App" not in res.data, res

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sorry! This app does not exists." in res.data, res.data

    def test_13a_hidden_applications_owner(self):
        """Test WEB hidden applications are shown to their owners"""
        self.register()
        self.new_application()
        self.update_application(new_hidden=True)

        res = self.app.get('/app/', follow_redirects=True)
        assert "Sample App" not in res.data, ("Applications should be hidden"
                                              "in the index")

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sample App" in res.data, ("Application should be shown to"
                                          "the owner")

    def test_14_delete_application(self):
        """Test WEB delete application works"""
        self.register()
        self.new_application()
        res = self.delete_application(method="GET")
        assert self.html_title("Application: Sample App &middot; Delete")\
                in res.data, res
        assert "No, do not delete it" in res.data, res

        res = self.delete_application()
        assert "Application deleted!" in res.data, res

    def test_15_twitter_email_warning(self):
        """Test WEB Twitter email warning works"""
        # This test assumes that the user allows Twitter to authenticate,
        #  returning a valid resp. The only difference is a user object
        #  without a password
        #  Register a user and sign out
        user = model.User(name="tester", passwd_hash="tester",
                          fullname="tester",
                          email_addr="tester")
        user.set_password('tester')
        db.session.add(user)
        db.session.commit()
        db.session.query(model.User).all()

        # Sign in again and check the warning message
        self.signin(email="tester", password="tester")
        res = self.app.get('/', follow_redirects=True)
        msg = "Please update your e-mail address in your profile page, " \
              "right now it is empty!"
        user = db.session.query(model.User).get(1)
        assert msg in res.data, res.data

    def test_16_task_status_completed(self):
        """Test WEB Task Status Completed works"""
        self.register()
        self.new_application()

        app = db.session.query(model.App).first()
        # We use a string here to check that it works too
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        self.signout()

        app = db.session.query(model.App).first()

        res = self.app.get('app/%s/tasks' % (app.short_name),
                           follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert 'Task <span class="label label-success">#1</span>'\
                in res.data, res.data
        assert '10 of 10' in res.data, res.data
        assert 'Download results' in res.data, res.data

    def test_17_export_task_runs(self):
        """Test WEB TaskRun export works"""
        self.register()
        self.new_application()

        app = db.session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()

        self.signout()

        app = db.session.query(model.App).first()
        res = self.app.get('app/%s/%s/results.json' % (app.short_name, 1),
                            follow_redirects=True)
        data = json.loads(res.data)
        assert len(data) == 10, data
        for tr in data:
            assert tr['info']['answer'] == 1, tr

    def test_18_task_status_wip(self):
        """Test WEB Task Status on going works"""
        self.register()
        self.new_application()

        app = db.session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        db.session.add(task)
        db.session.commit()
        self.signout()

        app = db.session.query(model.App).first()

        res = self.app.get('app/%s/tasks' % (app.short_name),
                           follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert 'Task <span class="label label-info">#1</span>'\
                in res.data, res.data
        assert '0 of 10' in res.data, res.data

    def test_19_app_index_categories(self):
        """Test WEB Application Index categories works"""
        self.register()
        self.new_application()
        self.signout()

        res = self.app.get('app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured" in res.data, res.data
        assert "Published" in res.data, res.data
        assert "Draft" in res.data, res.data

    def test_20_app_index_published(self):
        """Test WEB Application Index published works"""
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        info = dict(task_presenter="some html")
        app.info = info
        db.session.commit()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        db.session.add(task)
        db.session.commit()
        self.signout()

        res = self.app.get('app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "app-published" in res.data, res.data
        assert "app-draft" not in res.data, res.data
        assert "Sample App" in res.data, res.data

    def test_20_app_index_draft(self):
        """Test WEB Application Index draft works"""
        self.register()
        self.new_application()
        self.signout()

        res = self.app.get('/app/draft', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "app-published" not in res.data, res.data
        assert "app-draft" in res.data, res.data
        assert "Sample App" in res.data, res.data

    def test_21_get_specific_ongoing_task_anonymous(self):
        """Test WEB get specific ongoing task_id for
        an app works as anonymous"""

        Fixtures.create()
        self.delTaskRuns()
        app = db.session.query(model.App).first()
        task = db.session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()
        res = self.app.get('app/%s/task/%s' % (app.short_name, task.id),
                follow_redirects=True)
        assert 'TaskPresenter' in res.data, res.data
        assert "?next=%2Fapp%2F" + app.short_name +"%2Ftask%2F" + str(task.id),\
                res.data

    def test_22_get_specific_completed_task_anonymous(self):
        """Test WEB get specific completed task_id
        for an app works as anonymous"""

        model.rebuild_db()
        Fixtures.create()
        app = db.session.query(model.App).first()
        task = db.session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id,
                    task_id=task.id,
                    user_ip="127.0.0.1",
                    info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()

        ntask = model.Task(id=task.id, state='completed')

        assert ntask not in db.session
        db.session.merge(ntask)
        db.session.commit()

        res = self.app.get('app/%s/task/%s' % (app.short_name, task.id),
                follow_redirects=True)
        assert 'You have already participated in this task'\
                in res.data, res.data
        assert 'Try with another one' in res.data, res.data

    def test_23_get_specific_ongoing_task_user(self):
        """Test WEB get specific ongoing task_id for an app works as an user"""

        Fixtures.create()
        self.delTaskRuns()
        self.register()
        self.signin()
        app = db.session.query(model.App).first()
        task = db.session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()
        res = self.app.get('app/%s/task/%s' % (app.short_name, task.id),
                follow_redirects=True)
        assert 'TaskPresenter' in res.data, res.data
        self.signout()

    def test_24_get_specific_completed_task_user(self):
        """Test WEB get specific completed task_id
        for an app works as an user"""

        model.rebuild_db()
        Fixtures.create()
        self.register()

        user = db.session.query(model.User)\
                .filter(model.User.name == 'johndoe')\
                .first()
        app = db.session.query(model.App).first()
        task = db.session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()
        for i in range(10):
            task_run = model.TaskRun(app_id=app.id,
                    task_id=task.id,
                    user_id=user.id,
                    info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            #self.app.get('api/app/%s/newtask' % app.id)

        ntask = model.Task(id=task.id, state='completed')
        #self.signin()
        assert ntask not in db.session
        db.session.merge(ntask)
        db.session.commit()

        res = self.app.get('app/%s/task/%s' % (app.short_name, task.id),
                follow_redirects=True)
        assert 'You have already participated in this task'\
                in res.data, res.data
        assert 'Try with another one' in res.data, res.data
        self.signout()

    def test_25_get_wrong_task_app(self):
        """Test WEB get wrong task.id for an app works"""

        model.rebuild_db()
        Fixtures.create()
        app1 = db.session.query(model.App).get(1)
        app1_short_name = app1.short_name

        db.session.query(model.Task)\
                .filter(model.Task.app_id == 1)\
                .first()

        self.register()
        self.new_application()
        app2 = db.session.query(model.App).get(2)
        self.new_task(app2.id)
        task2 = db.session.query(model.Task)\
                .filter(model.Task.app_id == 2)\
                .first()
        task2_id = task2.id
        self.signout()

        res = self.app.get('/app/%s/task/%s' % (app1_short_name, task2_id))
        assert "Error" in res.data, res.data
        assert "This task does not belong to %s" % app1_short_name\
                in res.data, res.data

    def test_26_tutorial_signed_user(self):
        """Test WEB tutorials work as signed in user"""
        Fixtures.create()
        app1 = db.session.query(model.App).get(1)
        app1.info = dict(tutorial="some help")
        db.session.commit()
        self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" in res.data,\
                "There should be some tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data

    def test_27_tutorial_anonymous_user(self):
        """Test WEB tutorials work as an anonymous user"""
        Fixtures.create()
        app1 = db.session.query(model.App).get(1)
        app1.info = dict(tutorial="some help")
        db.session.commit()
        #self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        print res.data
        assert "some help" in res.data,\
                "There should be some tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data

    def test_28_non_tutorial_signed_user(self):
        """Test WEB app without tutorial work as signed in user"""
        Fixtures.create()
        db.session.commit()
        self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data,\
                "There should not be a tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data

    def test_29_tutorial_anonymous_user(self):
        """Test WEB app without tutorials work as an anonymous user"""
        Fixtures.create()
        db.session.commit()
        self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data,\
                "There should not be a tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data

    def test_30_app_id_owner(self):
        """Test WEB application settings page shows the ID to the owner"""
        self.register()
        self.new_application()

        res = self.app.get('/app/sampleapp/settings', follow_redirects=True)
        assert "Sample App" in res.data, ("Application should be shown to "
                                          "the owner")
        assert '<strong><i class="icon-cog"></i> ID</strong>: 1' in res.data,\
                "Application ID should be shown to the owner"

    def test_30_app_id_anonymous_user(self):
        """Test WEB application page does not show the ID to anonymous users"""
        self.register()
        self.new_application()
        self.signout()

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sample App" in res.data, ("Application name should be shown"
                                          " to users")
        assert '<strong><i class="icon-cog"></i> ID</strong>: 1' not in \
            res.data, "Application ID should be shown to the owner"

    def test_31_user_profile_progress(self):
        """Test WEB user progress profile page works"""
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        db.session.add(task)
        db.session.commit()
        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1, user_id=1,
                                     info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        res = self.app.get('account/profile', follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert "You have contributed <strong>10</strong> tasks" in res.data, res.data
        assert "Contribute!" in res.data, "There should be a Contribute button"

    def test_32_oauth_password(self):
        """Test WEB user sign in without password works"""
        user = model.User(
                email_addr="johndoe@johndoe.com",
                name="johndoe",
                passwd_hash=None,
                fullname="John Doe",
                api_key="api-key")
        db.session.add(user)
        db.session.commit()
        res = self.signin()
        assert "Ooops, we didn't find you in the system" in res.data, res.data

    @patch('pybossa.view.applications.requests.get')
    def test_33_bulk_csv_import_unauthorized(self, Mock):
        """Test WEB bulk import unauthorized works"""
        unauthorized_request = FakeRequest('Unauthorized', 403,
                                           {'content-type': 'text/csv'})
        Mock.return_value = unauthorized_request
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            'formtype': 'csv',
            }, follow_redirects=True)
        print res.data
        msg = "Oops! It looks like you don't have permission to access that file"
        assert msg in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_34_bulk_csv_import_non_html(self, Mock):
        """Test WEB bulk import non html works"""
        html_request = FakeRequest('Not a CSV', 200,
                                   {'content-type': 'text/html'})
        Mock.return_value = html_request
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            }, follow_redirects=True)
        assert "Oops! That file doesn't look like the right file." in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_35_bulk_csv_import_non_html(self, Mock):
        """Test WEB bulk import non html works"""
        empty_file = FakeRequest('CSV,with,no,content\n', 200,
                                 {'content-type': 'text/plain'})
        Mock.return_value = empty_file
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            'formtype': 'csv',
            }, follow_redirects=True)
        #print res.data
        assert "Oops! It looks like the file is empty." in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_36_bulk_csv_import_dup_header(self, Mock):
        """Test WEB bulk import duplicate header works"""
        empty_file = FakeRequest('Foo,Bar,Foo\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        Mock.return_value = empty_file
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            'formtype': 'csv',
            }, follow_redirects=True)
        assert "The file you uploaded has two headers with the same" \
                " name" in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_37_bulk_csv_import_no_column_names(self, Mock):
        """Test WEB bulk import no column names works"""
        empty_file = FakeRequest('Foo,Bar,Baz\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        Mock.return_value = empty_file
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            'formtype': 'csv',
            }, follow_redirects=True)
        task = db.session.query(model.Task).first()
        assert {u'Bar': u'2', u'Foo': u'1', u'Baz': u'3'} == task.info
        assert "Tasks imported successfully!" in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_38_bulk_csv_import_with_column_name(self, Mock):
        """Test WEB bulk import with column name works"""
        empty_file = FakeRequest('Foo,Bar,priority_0\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        Mock.return_value = empty_file
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'csv_url': 'http://myfakecsvurl.com',
            'formtype': 'csv',
            }, follow_redirects=True)
        task = db.session.query(model.Task).first()
        assert {u'Bar': u'2', u'Foo': u'1'} == task.info
        assert task.priority_0 == 3
        assert "Tasks imported successfully!" in res.data

    def test_39_google_oauth_creation(self):
        """Test WEB Google OAuth creation of user works"""
        fake_response = {
                u'access_token': u'access_token',
                u'token_type': u'Bearer',
                u'expires_in': 3600,
                u'id_token': u'token'}

        fake_user = {
        u'family_name': u'Doe', u'name': u'John Doe',
        u'picture': u'https://goo.gl/img.jpg',
        u'locale': u'en',
        u'gender': u'male',
        u'email': u'john@gmail.com',
        u'birthday': u'0000-01-15',
        u'link': u'https://plus.google.com/id',
        u'given_name': u'John',
        u'id': u'111111111111111111111',
        u'verified_email': True}

        from pybossa.view import google
        response_user = google.manage_user(fake_response['access_token'],
                fake_user, None)

        user = db.session.query(model.User)\
                .get(1)

        assert user.email_addr == response_user.email_addr, response_user

    def test_40_google_oauth_creation(self):
        """Test WEB Google OAuth detects same user name/email works"""
        fake_response = {
                u'access_token': u'access_token',
                u'token_type': u'Bearer',
                u'expires_in': 3600,
                u'id_token': u'token'}

        fake_user = {
        u'family_name': u'Doe', u'name': u'John Doe',
        u'picture': u'https://goo.gl/img.jpg',
        u'locale': u'en',
        u'gender': u'male',
        u'email': u'john@gmail.com',
        u'birthday': u'0000-01-15',
        u'link': u'https://plus.google.com/id',
        u'given_name': u'John',
        u'id': u'111111111111111111111',
        u'verified_email': True}

        self.register()
        self.signout()

        from pybossa.view import google
        response_user = google.manage_user(fake_response['access_token'],
                fake_user, None)

        assert response_user is None, response_user

    def test_39_facebook_oauth_creation(self):
        """Test WEB Facebook OAuth creation of user works"""
        fake_response = {
                u'access_token': u'access_token',
                u'token_type': u'Bearer',
                u'expires_in': 3600,
                u'id_token': u'token'}

        fake_user = {u'username': u'teleyinex',
                     u'first_name': u'John',
                     u'last_name': u'Doe',
                     u'verified': True,
                     u'name': u'John Doe',
                     u'locale': u'en_US',
                     u'gender': u'male',
                     u'email': u'johndoe@example.com',
                     u'quotes': u'"quote',
                     u'link': u'http://www.facebook.com/johndoe',
                     u'timezone': 1,
                     u'updated_time': u'2011-11-11T12:33:52+0000',
                     u'id': u'11111'}

        from pybossa.view import facebook
        response_user = facebook.manage_user(fake_response['access_token'],
                fake_user, None)

        user = db.session.query(model.User)\
                .get(1)

        assert user.email_addr == response_user.email_addr, response_user

    def test_40_facebook_oauth_creation(self):
        """Test WEB Facebook OAuth detects same user name/email works"""
        fake_response = {
                u'access_token': u'access_token',
                u'token_type': u'Bearer',
                u'expires_in': 3600,
                u'id_token': u'token'}

        fake_user = {u'username': u'teleyinex',
                     u'first_name': u'John',
                     u'last_name': u'Doe',
                     u'verified': True,
                     u'name': u'John Doe',
                     u'locale': u'en_US',
                     u'gender': u'male',
                     u'email': u'johndoe@example.com',
                     u'quotes': u'"quote',
                     u'link': u'http://www.facebook.com/johndoe',
                     u'timezone': 1,
                     u'updated_time': u'2011-11-11T12:33:52+0000',
                     u'id': u'11111'}

        self.register()
        self.signout()

        from pybossa.view import google
        response_user = google.manage_user(fake_response['access_token'],
                fake_user, None)

        assert response_user is None, response_user

    def test_39_twitter_oauth_creation(self):
        """Test WEB Twitter OAuth creation of user works"""
        fake_response = {
            u'access_token': {u'oauth_token': u'oauth_token',
                              u'oauth_token_secret': u'oauth_token_secret'},
            u'token_type': u'Bearer',
            u'expires_in': 3600,
            u'id_token': u'token'}

        fake_user = {u'screen_name': u'johndoe',
                     u'user_id': u'11111'}

        from pybossa.view import twitter
        response_user = twitter.manage_user(fake_response['access_token'],
                fake_user, None)

        user = db.session.query(model.User)\
                .get(1)

        assert user.email_addr == response_user.email_addr, response_user

    def test_40_twitter_oauth_creation(self):
        """Test WEB Twitter OAuth detects same user name/email works"""
        fake_response = {
            u'access_token': {u'oauth_token': u'oauth_token',
                              u'oauth_token_secret': u'oauth_token_secret'},
            u'token_type': u'Bearer',
            u'expires_in': 3600,
            u'id_token': u'token'}

        fake_user = {u'screen_name': u'johndoe',
                     u'user_id': u'11111'}

        self.register()
        self.signout()

        from pybossa.view import twitter
        response_user = twitter.manage_user(fake_response['access_token'],
                fake_user, None)

        assert response_user is None, response_user

    def test_41_password_change(self):
        """Test password changing"""
        password = "mehpassword"
        self.register(password=password)
        res = self.app.post('/account/profile/password', data={
            'current_password': password,
            'new_password': "p4ssw0rd",
            'confirm': "p4ssw0rd",
            }, follow_redirects=True)
        assert "Yay, you changed your password succesfully!" in res.data

        password = "mehpassword"
        self.register(password=password)
        res = self.app.post('/account/profile/password', data={
            'current_password': "wrongpassword",
            'new_password': "p4ssw0rd",
            'confirm': "p4ssw0rd",
            }, follow_redirects=True)
        assert "Your current password doesn't match the one in our records" in res.data

    def test_42_password_link(self):
        """Test visibility of password change link"""
        self.register()
        res = self.app.get('/account/profile/settings')
        assert "Change your Password" in res.data
        user = model.User.query.get(1)
        user.twitter_user_id = 1234
        db.session.add(user)
        db.session.commit()
        res = self.app.get('/account/profile/settings')
        assert "Change your Password" not in res.data, res.data

    def test_43_terms_of_use_and_data(self):
        """Test WEB terms of use is working"""
        res = self.app.get('account/signin', follow_redirects=True)
        assert "/help/terms-of-use" in res.data, res.data
        assert "http://opendatacommons.org/licenses/by/" in res.data, res.data

        res = self.app.get('account/register', follow_redirects=True)
        assert "http://okfn.org/terms-of-use/" in res.data, res.data
        assert "http://opendatacommons.org/licenses/by/" in res.data, res.data

    @patch('pybossa.view.account.signer.loads')
    def test_44_password_reset_key_errors(self, Mock):
        """Test WEB password reset key errors are caught"""
        self.register()
        user = model.User.query.get(1)
        userdict = {'user': user.name, 'password': user.passwd_hash}
        fakeuserdict = {'user': user.name, 'password': 'wronghash'}
        key = signer.dumps(userdict, salt='password-reset')
        returns = [BadSignature('Fake Error'), BadSignature('Fake Error'), userdict,
                   fakeuserdict, userdict]
        def side_effects(*args, **kwargs):
            result = returns.pop(0)
            if isinstance(result, BadSignature):
                raise result
            return result
        Mock.side_effect = side_effects
        # Request with no key
        res = self.app.get('/account/reset-password', follow_redirects=True)
        assert 403 == res.status_code
        # Request with invalid key
        res = self.app.get('/account/reset-password?key=foo', follow_redirects=True)
        assert 403 == res.status_code
        # Request with key exception
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 403 == res.status_code
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 200 == res.status_code
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 403 == res.status_code
        res = self.app.post('/account/reset-password?key=%s' % (key), data={
                'new_password': 'p4ssw0rD',
                'confirm': 'p4ssw0rD'
                }, follow_redirects=True)
        assert "You reset your password successfully!" in res.data

    def test_45_password_reset_link(self):
        """Test WEB password reset email form"""
        res = self.app.post('/account/forgot-password', data={
                'email_addr': 'johndoe@example.com'
                }, follow_redirects=True)
        assert ("We don't have this email in our records. You may have"
               " signed up with a different email or used Twitter, "
               "Facebook, or Google to sign-in") in res.data

        self.register()
        self.register(username='janedoe')
        jane = model.User.query.get(2)
        jane.twitter_user_id = 10
        db.session.add(jane)
        db.session.commit()
        # TODO: This is a hack to get tests working. Documented method to
        # supress mail sending doesn't seem to work
        mail.suppress = True
        with mail.record_messages() as outbox:
            self.app.post('/account/forgot-password', data={
                'email_addr': 'johndoe@example.com'
                }, follow_redirects=True)
            self.app.post('/account/forgot-password', data={
                'email_addr': 'janedoe@example.com'
                }, follow_redirects=True)
            assert 'Click here to recover your account' in outbox[0].body
            assert 'your Twitter account to ' in outbox[1].body

    def test_46_task_presenter_editor_exists(self):
        """Test WEB task presenter editor is an option"""
        self.register()
        self.new_application()
        res = self.app.get('/app/sampleapp/settings', follow_redirects=True)
        assert "Edit the task presenter" in res.data, \
            "Task Presenter Editor should be an option"

    def test_47_task_presenter_editor_loads(self):
        """Test WEB task presenter editor loads"""
        self.register()
        self.new_application()
        res = self.app.get('/app/sampleapp/taskpresentereditor',
                           follow_redirects=True)
        err_msg = "Task Presenter options not found"
        assert "Task Presenter Editor" in res.data, err_msg
        err_msg = "Basic template not found"
        assert "The most basic template" in res.data, err_msg
        err_msg = "Image Pattern Recognition not found"
        assert "Flickr Person Finder template" in res.data, err_msg
        err_msg = "Geo-coding"
        assert "Urban Park template" in res.data, err_msg
        err_msg = "Transcribing documents"
        assert "PDF transcription template" in res.data, err_msg

    def test_48_task_presenter_editor_works(self):
        """Test WEB task presenter editor works"""
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        assert not app.info.get('task_presenter'), \
                "Task Presenter should be empty"
        res = self.app.get('/app/sampleapp/taskpresentereditor?template=basic',
                           follow_redirects=True)
        assert "var editor" in res.data, "CodeMirror Editor not found"
        assert "Task Presenter" in res.data, "CodeMirror Editor not found"
        assert "Task Presenter Preview" in res.data, "CodeMirror View not found"
        res = self.app.post('/app/sampleapp/taskpresentereditor',
                            data={'editor': 'Some HTML code!'},
                            follow_redirects=True)
        assert "Sample App" in res.data, "Does not return to app details"
        app = db.session.query(model.App).first()
        assert app.info['task_presenter'] == 'Some HTML code!', \
                "Task Presenter failed to update"

    def test_48_update_app_info(self):
        """Test WEB app update/edit works keeping previous info values"""
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        assert not app.info.get('task_presenter'), \
                "Task Presenter should be empty"
        res = self.app.post('/app/sampleapp/taskpresentereditor',
                            data={'editor': 'Some HTML code!'},
                            follow_redirects=True)
        assert "Sample App" in res.data, "Does not return to app details"
        app = db.session.query(model.App).first()
        for i in range(10):
            key = "key_%s" % i
            app.info[key] = i
        db.session.add(app)
        db.session.commit()
        _info = app.info

        self.update_application()
        app = db.session.query(model.App).first()
        print app.info
        print _info
        for key in _info:
            assert key in app.info.keys(), \
                "The key %s is lost and it should be here" % key
        assert app.name == "Sample App", "The app has not been updated"
        error_msg = "The app description has not been updated"
        assert app.description == "Description", error_msg
        error_msg = "The app icon has not been updated"
        assert app.info['thumbnail'] == "New Icon link", error_msg
        error_msg = "The app long description has not been updated"
        assert app.long_description == "Long desc", error_msg
        assert app.info['sched'] == "random", "The app sched has not been updated"

    def test_49_announcement_messages(self):
        """Test WEB announcement messages works"""
        self.register()
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should be a message for the root user"
        assert "Root Message" in res.data, error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in res.data, error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in res.data, error_msg
        # Now make the user an app owner
        self.new_application()
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should be a message for the root user"
        assert "Root Message" in res.data, error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in res.data, error_msg
        error_msg = "There should be an owner message"
        assert "Owner Message" in res.data, error_msg
        self.signout()

        # Register another user
        self.register(method="POST", fullname="Jane Doe", username="janedoe",
                      password="janedoe", password2="janedoe",
                      email="jane@jane.com")
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should not be a message for the root user"
        assert "Root Message" not in res.data, error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in res.data, error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in res.data, error_msg
        self.signout()

        # Now as an anonymous user
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should not be a message for the root user"
        assert "Root Message" not in res.data, error_msg
        error_msg = "There should not be a message for the user"
        assert "User Message" not in res.data, error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in res.data, error_msg

    def test_50_export_task_json(self):
        """Test WEB export Tasks to JSON works"""
        Fixtures.create()
        # First test for a non-existant app
        uri = '/app/somethingnotexists/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/app/somethingnotexists/export?type=task&format=json"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real app
        uri = '/app/%s/export' % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "<strong>%s</strong>: Export All Tasks and Task Runs" % Fixtures.app_name
        assert heading in res.data, "Export page should be available\n %s" % res.data
        # Now test that a 404 is raised when an arg is invalid
        uri = "/app/%s/export?type=ask&format=json" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/app/%s/export?type=task&format=gson" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/app/%s/export?format=json" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/app/%s/export?type=task" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now get the tasks in JSON format
        uri = "/app/%s/export?type=task&format=json" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        exported_tasks = json.loads(res.data)
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .first()
        err_msg = "The number of exported tasks is different from App Tasks"
        assert len(exported_tasks) == len(app.tasks), err_msg

    def test_51_export_taskruns_json(self):
        """Test WEB export Task Runs to JSON works"""
        Fixtures.create()
        # First test for a non-existant app
        uri = '/app/somethingnotexists/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/app/somethingnotexists/export?type=taskrun&format=json"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real app
        uri = '/app/%s/export' % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "<strong>%s</strong>: Export All Tasks and Task Runs" % Fixtures.app_name
        assert heading in res.data, "Export page should be available\n %s" % res.data
        # Now get the tasks in JSON format
        uri = "/app/%s/export?type=task_run&format=json" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        exported_task_runs = json.loads(res.data)
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .first()
        err_msg = "The number of exported task runs is different from App Tasks"
        assert len(exported_task_runs) == len(app.task_runs), err_msg

    def test_52_export_task_csv(self):
        """Test WEB export Tasks to CSV works"""
        Fixtures.create()
        # First test for a non-existant app
        uri = '/app/somethingnotexists/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/app/somethingnotexists/export?type=task&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real app
        uri = '/app/%s/export' % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "<strong>%s</strong>: Export All Tasks and Task Runs" % Fixtures.app_name
        assert heading in res.data, "Export page should be available\n %s" % res.data
        # Now get the tasks in JSON format
        uri = "/app/%s/export?type=task&format=csv" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        csv_content = StringIO.StringIO(res.data)
        csvreader = unicode_csv_reader(csv_content)
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .first()
        exported_tasks = []
        n = 0
        for row in csvreader:
            if n != 0:
                exported_tasks.append(row)
            n = n + 1
        err_msg = "The number of exported tasks is different from App Tasks"
        assert len(exported_tasks) == len(app.tasks), err_msg

    def test_53_export_task_runs_csv(self):
        """Test WEB export Task Runs to CSV works"""
        Fixtures.create()
        # First test for a non-existant app
        uri = '/app/somethingnotexists/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/app/somethingnotexists/export?type=tas&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real app
        uri = '/app/%s/export' % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "<strong>%s</strong>: Export All Tasks and Task Runs" % Fixtures.app_name
        assert heading in res.data, "Export page should be available\n %s" % res.data
        # Now get the tasks in JSON format
        uri = "/app/%s/export?type=task_run&format=csv" % Fixtures.app_short_name
        res = self.app.get(uri, follow_redirects=True)
        csv_content = StringIO.StringIO(res.data)
        csvreader = unicode_csv_reader(csv_content)
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .first()
        exported_task_runs = []
        n = 0
        for row in csvreader:
            if n != 0:
                exported_task_runs.append(row)
            n = n + 1
        err_msg = "The number of exported task runs is different \
                   from App Tasks Runs"
        assert len(exported_task_runs) == len(app.task_runs), err_msg

    def test_54_import_tasks(self):
        # there's a bug in the test framework:
        # self.app.get somehow calls render_template twice
        return
        """Test WEB import Task templates should work"""
        self.register()
        self.new_application()
        # Without tasks, there should be a template
        res = self.app.get('/app/sampleapp/import', follow_redirects=True)
        err_msg = "There should be a Basic template"
        assert "template=csv" in res.data, err_msg
        err_msg = "There should be an Image template"
        assert "mode=image" in res.data, err_msg
        err_msg = "There should be a Map template"
        assert "mode=map" in res.data, err_msg
        err_msg = "There should be a PDF template"
        assert "mode=pdf" in res.data, err_msg
        # With tasks
        self.new_task(1)
        res = self.app.get('/app/sampleapp/import', follow_redirects=True)
        err_msg = "There should load directly the basic template"
        err_msg = "There should not be a Basic template"
        assert "template=basic" not in res.data, err_msg
        err_msg = "There should not be an Image template"
        assert "template=image" not in res.data, err_msg
        err_msg = "There should not be a Map template"
        assert "template=map" not in res.data, err_msg
        err_msg = "There should not be a PDF template"
        assert "template=pdf" not in res.data, err_msg

    def test_55_facebook_account_warning(self):
        """Test WEB Facebook OAuth user gets a hint to sign in"""
        user = model.User(fullname='John',
                          name='john',
                          email_addr='john@john.com',
                          info={})

        user.info = dict(facebook_token=u'facebook')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'facebook' but returned %s" % method
        assert method == 'facebook', err_msg

        user.info = dict(google_token=u'google')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'google' but returned %s" % method
        assert method == 'google', err_msg

        user.info = dict(twitter_token=u'twitter')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'twitter' but returned %s" % method
        assert method == 'twitter', err_msg

        user.info = {}
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'local' but returned %s" % method
        assert method == 'local', err_msg

    def test_56_delete_tasks(self):
        """Test WEB delete tasks works"""
        Fixtures.create()
        # Anonymous user
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in res.data, err_msg
        err_msg = "Anonymous user should not be allowed to delete tasks"
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Anonymous user should not be allowed to delete tasks"
        assert "Please sign in to access this page" in res.data, err_msg

        # Authenticated user but not owner
        self.register()
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in GET"
        assert res.status == '403 FORBIDDEN', err_msg
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in POST"
        assert res.status == '403 FORBIDDEN', err_msg
        self.signout()

        # Owner
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        res = self.signin(email=u'tester@tester.com', password=u'tester')
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Owner user should get 200 in GET"
        assert res.status == '200 OK', err_msg
        assert len(tasks) > 0, "len(app.tasks) > 0"
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Owner should get 200 in POST"
        assert res.status == '200 OK', err_msg
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        assert len(tasks) == 0, "len(app.tasks) != 0"

        # Admin
        res = self.signin(email=u'root@root.com', password=u'tester' + 'root')
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg

    def test_57_reset_api_key(self):
        """Test WEB reset api key works"""
        url = "/account/profile/resetapikey"
        # Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in res.data, err_msg
        res = self.app.post(url, follow_redirects=True)
        assert "Please sign in to access this page" in res.data, err_msg

        # Authenticated user
        self.register()
        user = db.session.query(model.User).get(1)
        api_key = user.api_key
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Authenticated user should get access to reset api key page"
        assert res.status_code == 200, err_msg
        assert "Reset API Key" in res.data, err_msg
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Authenticated user should be able to reset his api key"
        assert res.status_code == 200, err_msg
        user = db.session.query(model.User).get(1)
        err_msg = "New generated API key should be different from old one"
        assert api_key != user.api_key, err_msg

    def test_58_global_stats(self):
        """Test WEB global stats of the site works"""
        url = "/stats"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a Global Statistics page of the project"
        assert "General Statistics" in res.data, err_msg

    def test_59_help_api(self):
        """Test WEB help api page exists"""
        Fixtures.create()
        url = "/help/api"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a help api.html page"
        assert "API Help" in res.data, err_msg

    def test_69_allow_anonymous_contributors(self):
        """Test WEB allow anonymous contributors works"""
        Fixtures.create()
        app = db.session.query(model.App).first()
        url = '/app/%s/newtask' % app.short_name

        # All users are allowed to participate by default
        # As Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The anonymous user should be able to participate"
        assert app.name in res.data, err_msg

        # As registered user
        self.register()
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The anonymous user should be able to participate"
        assert app.name in res.data, err_msg
        self.signout()

        # Now only allow authenticated users
        app.allow_anonymous_contributors = False
        db.session.add(app)
        db.session.commit()

        # As Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should be redirected to sign in"
        msg = "Oops! You have to sign in to participate in <strong>%s</strong>" % app.name
        assert msg in res.data, err_msg

        # As registered user
        res = self.signin()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The authenticated user should be able to participate"
        assert app.name in res.data, err_msg
        self.signout()

    def test_70_public_user_profile(self):
        """Test WEB public user profile works"""
        Fixtures.create()

        # Should work as an anonymous user
        url = '/account/%s/' % Fixtures.name
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a public profile page for the user"
        assert Fixtures.fullname in res.data, err_msg

        # Should work as an authenticated user
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        assert Fixtures.fullname in res.data, err_msg

    @patch('pybossa.view.applications.requests.get')
    def test_71_bulk_epicollect_import_unauthorized(self, Mock):
        """Test WEB bulk import unauthorized works"""
        unauthorized_request = FakeRequest('Unauthorized', 403,
                                           {'content-type': 'application/json'})
        Mock.return_value = unauthorized_request
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'epicollect_project': 'fakeproject',
            'epicollect_form': 'fakeform',
            'formtype': 'json',
            }, follow_redirects=True)
        print res.data
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"
        assert msg in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_72_bulk_epicollect_import_non_html(self, Mock):
        """Test WEB bulk import non html works"""
        html_request = FakeRequest('Not an application/json', 200,
                                   {'content-type': 'text/html'})
        Mock.return_value = html_request
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import?template=csv' % (app.short_name)), data={
            'epicollect_project': 'fakeproject',
            'epicollect_form': 'fakeform',
            'formtype': 'json',
            }, follow_redirects=True)
        print res.data
        assert "Oops! That project and form do not look like the right one." in res.data

    @patch('pybossa.view.applications.requests.get')
    def test_73_bulk_epicollect_import_json(self, Mock):
        """Test WEB bulk import json works"""
        data = [dict(DeviceID=23)]
        html_request = FakeRequest(json.dumps(data), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        self.register()
        self.new_application()
        app = db.session.query(model.App).first()
        res = self.app.post(('/app/%s/import' % (app.short_name)),
                            data={'epicollect_project': 'fakeproject',
                                  'epicollect_form': 'fakeform',
                                  'formtype': 'json'},
                            follow_redirects=True)

        err_msg = "Tasks should be imported"
        #print res.data
        assert "Tasks imported successfully!" in res.data, err_msg
        tasks = db.session.query(model.Task).filter_by(app_id=app.id).all()
        err_msg = "The imported task from EpiCollect is wrong"
        assert tasks[0].info['DeviceID'] == 23, err_msg
