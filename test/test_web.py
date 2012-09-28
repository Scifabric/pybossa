import json

from base import web, model, Fixtures


class TestWeb:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        #Fixtures.create()

    def tearDown(self):
        model.Session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Helper functions
    def html_title(self, title=None):
        """Helper function to create an HTML title"""
        if title == None:
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

    def profile(self):
        """Helper function to check profile of signed in user"""
        return self.app.get("/account/profile", follow_redirects=True)

    def update_profile(self, method="POST", id=1, fullname="John Doe",
                       name="johndoe", email_addr="johndoe@example.com"):
        """Helper function to update the profile of users"""
        if (method == "POST"):
            return self.app.post("/account/profile/update", data={
                    'id': id,
                    'fullname': fullname,
                    'name': name,
                    'email_addr': email_addr
                }, follow_redirects=True)
        else:
            return self.app.get("/account/profile/update",
                                follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)

    def new_application(self, method="POST", name="Sample App",
            short_name="sampleapp", description="Description",
            long_description=u'<div id="long_desc">Long desc</div>',
            hidden=False):
        """Helper function to create an application"""
        if method == "POST":
            if hidden:
                return self.app.post("/app/new", data={
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'long_description': long_description,
                    'hidden': hidden,
                }, follow_redirects=True)
            else:
                return self.app.post("/app/new", data={
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'long_description': long_description,
                }, follow_redirects=True)
        else:
            return self.app.get("/app/new", follow_redirects=True)

    def new_task(self, appid):
        """Helper function to create tasks for an app"""
        tasks = []
        for i in range(0, 10):
            tasks.append(model.Task(app_id=appid, state='0', info={}))
        model.Session.add_all(tasks)
        model.Session.commit()

    def delTaskRuns(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        model.Session.query(model.TaskRun).filter_by(app_id=1).delete()
        model.Session.commit()

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
                           new_long_description="Long desc",
                           new_hidden=False):
        """Helper function to create an application"""
        if method == "POST":
            if new_hidden:
                return self.app.post("/app/%s/update" % short_name, data={
                        'id': id,
                        'name': new_name,
                        'short_name': new_short_name,
                        'description': new_description,
                        'hidden': new_hidden,
                    }, follow_redirects=True)
            else:
                return self.app.post("/app/%s/update" % short_name, data={
                        'id': id,
                        'name': new_name,
                        'short_name': new_short_name,
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
        assert "Create your own application" in res.data, res

    def test_02_stats(self):
        """Test WEB leaderboard or stats page works"""
        self.register()
        self.new_application()

        app = model.Session.query(model.App).first()
        # We use a string here to check that it works too
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        model.Session.add(task)
        model.Session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        self.signout()

        res = self.app.get('/stats', follow_redirects=True)
        assert self.html_title("Leaderboard") in res.data, res
        assert "Most active applications" in res.data, res
        assert "Most active volunteers" in res.data, res
        assert "Sample App" in res.data, res


    def test_02a_stats_hidden_apps(self):
        """Test WEB leaderboard does not show hidden apps"""
        self.register()
        self.new_application()

        app = model.Session.query(model.App).first()
        # We use a string here to check that it works too
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        model.Session.add(task)
        model.Session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        self.update_application(new_hidden=True)
        self.signout()

        res = self.app.get('/stats', follow_redirects=True)
        assert self.html_title("Leaderboard") in res.data, res
        assert "Most active applications" in res.data, res
        assert "Most active volunteers" in res.data, res
        assert "Sample App" not in res.data, res


    def test_03_register(self):
        """Test WEB register user works"""
        res = self.register(method="GET")
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert self.html_title("Register") in res.data, res

        res = self.register()
        assert self.html_title() in res.data, res
        assert "Thanks for signing-up" in res.data, res

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

        res = self.signin(username='')
        assert "Please correct the errors" in  res.data, res
        assert "The username is required" in res.data, res

        res = self.signin(password='')
        assert "Please correct the errors" in  res.data, res
        assert "You must provide a password" in res.data, res

        res = self.signin(username='', password='')
        assert "Please correct the errors" in  res.data, res
        assert "The username is required" in res.data, res
        assert "You must provide a password" in res.data, res

        res = self.signin(username='wrongusername')
        assert "Incorrect email/password" in  res.data, res

        res = self.signin(password='wrongpassword')
        assert "Incorrect email/password" in  res.data, res

        res = self.signin(username='wrongusername', password='wrongpassword')
        assert "Incorrect email/password" in  res.data, res

        res = self.signin()
        assert self.html_title() in res.data, res
        assert "Welcome back John Doe" in res.data, res

        # Check profile page with several information chunks
        res = self.profile()
        assert self.html_title("Profile") in res.data, res
        assert "John Doe" in res.data, res
        assert "johndoe@example.com" in res.data, res
        assert "API key" in res.data, res
        assert "Create a new application" in res.data, res

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
        assert "API key" in res.data, res

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

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com")
        assert self.html_title("Profile") in res.data, res
        assert "Your profile has been updated!" in res.data, res
        assert "John Doe 2" in res.data, res
        assert "johndoe" in res.data, res
        assert "johndoe2@example.com" in res.data, res

        # Updating the username field forces the user to re-log in
        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  name="johndoe2")
        assert "Your profile has been updated!" in res.data, res
        assert "Please sign in to access this page" in res.data, res

        res = self.signin(method="POST", username="johndoe2",
                          password="p4ssw0rd",
                          next="%2Faccount%2Fprofile")
        assert "Welcome back John Doe 2" in res.data, res
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
        res = self.app.get('/app/nonapp')
        assert res.status == '404 NOT FOUND', res.status

    def test_06_applications(self):
        """Test WEB applications index interface works"""
        # Check first without apps
        res = self.app.get('/app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured" in res.data, res.data
        assert "Published" in res.data, res.data
        assert "Draft" in res.data, res.data
        assert "Create an application!" in res.data, res.data

        self.register()
        self.new_application()
        self.new_task(1)

        self.signout()

        res = self.app.get('/app/')
        assert self.html_title("Applications") in res.data, res.data
        assert "Applications" in res.data, res.data
        assert '/app/sampleapp' in res.data, res.data

    def test_07_index_one_app(self):
        """Test WEB index Featured for one registered application works"""
        # With one application in the system
        self.register()
        self.new_application()
        apps = model.Session.query(model.App)\
                .all()
        assert len(apps) == 1,\
                "There should be only 1 app, but there are %s" % len(apps)
        featured_apps = []
        for a in apps:
            f = model.Featured()
            f.app_id = a.id
            featured_apps.append(f)
        assert len(featured_apps) == 1,\
                "There should be only 1 app, but there are %s" % len(apps)
        model.Session.add_all(featured_apps)
        model.Session.commit()
        self.new_task(1)
        self.signout()
        res = self.app.get('/')
        assert "Featured applications" in res.data, res.data
        assert "Sample App" in res.data, res.data
        assert "Try it!" in res.data, res.data
        assert "Your application" in res.data, res.data
        assert "Could be here!" in res.data, res.data
        assert "Create an application!" in res.data, res.data

    def test_08_index_two_apps(self):
        """Test WEB index Featured for two registered applications works"""
        # With one application in the system
        self.register()
        self.new_application()
        self.new_task(1)
        self.new_application(name="New App", short_name="newapp",
                             description="New description")
        self.new_task(2)
        self.signout()
        apps = model.Session.query(model.App)\
                .all()
        assert len(apps) == 2,\
                "There should be only 2 apps, but there are %s" % len(apps)
        featured_apps = []
        for a in apps:
            f = model.Featured()
            f.app_id = a.id
            featured_apps.append(f)
        assert len(featured_apps) == 2,\
                "There should be only 2 app, but there are %s" % len(apps)
        model.Session.add_all(featured_apps)
        model.Session.commit()

        res = self.app.get('/')
        assert "Featured applications" in res.data, res.data
        # First app
        assert "Sample App" in res.data, res.data
        assert "Description" in res.data, res.data
        assert "Try it!" in res.data, res.data
        # Second app
        assert "New App" in res.data, res.data
        assert "New description" in res.data, res.data
        assert "Try it!" in res.data, res.data
        # Create application demo
        assert "Your application" in res.data, res.data
        assert "Could be here!" in res.data, res.data
        assert "Create an application!" in res.data, res.data

    def test_09_index_three_apps(self):
        """Test WEB index Featured for three registered applications works"""
        # With one application in the system
        self.register()
        self.new_application()
        self.new_task(1)
        self.new_application(name="New App", short_name="newapp",
                             description="New description")
        self.new_task(2)
        self.new_application(name="Third App", short_name="thirdapp",
                             description="Third description")
        self.new_task(3)
        self.signout()
        apps = model.Session.query(model.App)\
                .all()
        assert len(apps) == 3,\
                "There should be only 3 apps, but there are %s" % len(apps)
        featured_apps = []
        for a in apps:
            f = model.Featured()
            f.app_id = a.id
            featured_apps.append(f)
        assert len(featured_apps) == 3,\
                "There should be only 3 app, but there are %s" % len(apps)
        model.Session.add_all(featured_apps)
        model.Session.commit()

        res = self.app.get('/')
        assert "Featured applications" in res.data, res.data
        # First app
        assert "Sample App" in res.data, res.data
        assert "Description" in res.data, res.data
        assert "Try it!" in res.data, res.data
        # Second app
        assert "New App" in res.data, res.data
        assert "New description" in res.data, res.data
        assert "Try it!" in res.data, res.data
        # Create application demo
        assert "Third App" in res.data, res.data
        assert "Third description" in res.data, res.data
        assert "Try it!" in res.data, res.data
        # Big black button
        assert "Create your own application" in res.data, res.data

    def test_10_get_application(self):
        """Test WEB application URL/<short_name> works"""
        # Sign in and create an application
        self.register()
        res = self.new_application()

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App")\
                in res.data, res
        assert "Long desc" in res.data, res
        assert "Summary" in res.data, res
        assert "Overall progress" in res.data, res
        assert "Tasks" in res.data, res
        assert "Edit the application" in res.data, res
        assert "Delete the application" in res.data, res
        self.signout()

        # Now as an anonymous user
        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Long desc" in res.data, res
        assert "Summary" in res.data, res
        assert "Overall progress" in res.data, res
        assert "Tasks" in res.data, res
        assert "Edit the application" not in res.data, res
        assert "Delete the application" not in res.data, res

        # Now with a different user
        self.register(fullname="Perico Palotes", username="perico")
        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Long desc" in res.data, res
        assert "Summary" in res.data, res
        assert "Overall progress" in res.data, res
        assert "Edit the application" not in res.data, res
        assert "Delete the application" not in res.data, res

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
        assert self.html_title("New Application") in res.data, res
        assert "Create the application" in res.data, res

        res = self.new_application()
        assert self.html_title("Application: %s" % "Sample App")\
                in res.data, res
        assert "Application created!" in res.data, res

    def test_12_update_application(self):
        """Test WEB update application works"""
        self.register()
        self.new_application()

        # Get the Update App web page
        res = self.update_application(method="GET")
        assert self.html_title("Update the application: Sample App")\
                in res.data, res
        assert 'input id="id" name="id" type="hidden" value="1"'\
                in res.data, res
        assert "Save the changes" in res.data, res

        # Update the application
        res = self.update_application(new_name="New Sample App",
                                      new_short_name="newshortname",
                                      new_description="New description",
                                      new_long_description=u'New long desc',
                                      new_hidden=True)
        #assert self.html_title("Application: New Sample App") in res.data, res.data
        assert "Application updated!" in res.data, res

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
        assert "Sample App" not in res.data, "Applications should be hidden in the index"

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sample App" in res.data, "Application should be shown to the owner"


    def test_14_delete_application(self):
        """Test WEB delete application works"""
        self.register()
        self.new_application()
        res = self.delete_application(method="GET")
        assert self.html_title("Delete Application: Sample App")\
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
                          email_addr="tester")
        user.set_password('tester')
        model.Session.add(user)
        model.Session.commit()
        model.Session.query(model.User).all()

        # Sign in again and check the warning message
        self.signin(username="tester", password="tester")
        res = self.app.get('/', follow_redirects=True)
        msg = "Please update your e-mail address in your profile page, " \
              "right now it is empty!"
        user = model.Session.query(model.User).get(1)
        assert msg in res.data, res.data

    def test_16_task_status_completed(self):
        """Test WEB Task Status Completed works"""
        self.register()
        self.new_application()

        app = model.Session.query(model.App).first()
        # We use a string here to check that it works too
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        model.Session.add(task)
        model.Session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        self.signout()

        app = model.Session.query(model.App).first()

        res = self.app.get('app/' + app.short_name + "/tasks", follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert 'Task <span class="label label-success">#1</span>'\
                in res.data, res.data
        assert '10 of 10' in res.data, res.data
        assert 'Download results' in res.data, res.data

    def test_17_export_task_runs(self):
        """Test WEB TaskRun export works"""
        self.register()
        self.new_application()

        app = model.Session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        model.Session.add(task)
        model.Session.commit()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1,
                                     info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()

        self.signout()

        app = model.Session.query(model.App).first()
        res = self.app.get('app/%s/%s/results.json' % (app.id, 1),
                            follow_redirects=True)
        data = json.loads(res.data)
        assert len(data) == 10, data
        for tr in data:
            assert tr['info']['answer'] == 1, tr

    def test_18_task_status_wip(self):
        """Test WEB Task Status on going works"""
        self.register()
        self.new_application()

        app = model.Session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        model.Session.add(task)
        model.Session.commit()
        self.signout()

        app = model.Session.query(model.App).first()

        res = self.app.get('app/' + app.short_name + "/tasks", follow_redirects=True)
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
        app = model.Session.query(model.App).first()
        info = dict(task_presenter="some html")
        app.info = info
        model.Session.commit()
        task = model.Task(app_id=app.id, info={'n_answers': 10})
        model.Session.add(task)
        model.Session.commit()
        self.signout()

        res = self.app.get('app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured</h2>" not in res.data, res.data
        assert "Published</h2>" in res.data, res.data
        assert "Draft</h2>" not in res.data, res.data

    def test_20_app_index_featured(self):
        """Test WEB Application Index featured works"""
        self.register()
        self.new_application()
        app = model.Session.query(model.App).first()
        info = dict(task_presenter="some html")
        app.info = info
        model.Session.commit()

        f = model.Featured()
        f.app_id = app.id
        model.Session.add(f)
        model.Session.commit()

        task = model.Task(app_id=app.id, info={'n_answers': 10})
        model.Session.add(task)
        model.Session.commit()
        self.signout()

        res = self.app.get('app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured</h2>" in res.data, res.data
        assert "Published</h2>" not in res.data, res.data
        assert "Draft</h2>" not in res.data, res.data

    def test_20_app_index_draft(self):
        """Test WEB Application Index draft works"""
        self.register()
        self.new_application()
        self.signout()

        res = self.app.get('app', follow_redirects=True)
        assert "Applications" in res.data, res.data
        assert "Featured</h2>" not in res.data, res.data
        assert "Published</h2>" not in res.data, res.data
        assert "Draft</h2>" in res.data, res.data

    def test_21_get_specific_ongoing_task_anonymous(self):
        """Test WEB get specific ongoing task_id for
        an app works as anonymous"""

        Fixtures.create()
        self.delTaskRuns()
        app = model.Session.query(model.App).first()
        task = model.Session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()
        res = self.app.get('app/%s/task/%s' % (app.short_name, task.id),
                follow_redirects=True)
        assert 'TaskPresenter' in res.data, res.data

    def test_22_get_specific_completed_task_anonymous(self):
        """Test WEB get specific completed task_id
        for an app works as anonymous"""

        model.rebuild_db()
        Fixtures.create()
        app = model.Session.query(model.App).first()
        task = model.Session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()

        for i in range(10):
            task_run = model.TaskRun(app_id=app.id,
                    task_id=task.id,
                    user_ip="127.0.0.1",
                    info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()

        ntask = model.Task(id=task.id, state='completed')

        assert ntask not in model.Session
        model.Session.merge(ntask)
        model.Session.commit()

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
        app = model.Session.query(model.App).first()
        task = model.Session.query(model.Task)\
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

        user = model.Session.query(model.User)\
                .filter(model.User.name == 'johndoe')\
                .first()
        app = model.Session.query(model.App).first()
        task = model.Session.query(model.Task)\
                .filter(model.App.id == app.id)\
                .first()
        for i in range(10):
            task_run = model.TaskRun(app_id=app.id,
                    task_id=task.id,
                    user_id=user.id,
                    info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()
            #self.app.get('api/app/%s/newtask' % app.id)

        ntask = model.Task(id=task.id, state='completed')
        #self.signin()
        assert ntask not in model.Session
        model.Session.merge(ntask)
        model.Session.commit()

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
        app1 = model.Session.query(model.App).get(1)
        app1_short_name = app1.short_name

        model.Session.query(model.Task)\
                .filter(model.Task.app_id == 1)\
                .first()

        self.register()
        self.new_application()
        app2 = model.Session.query(model.App).get(2)
        self.new_task(app2.id)
        task2 = model.Session.query(model.Task)\
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
        app1 = model.Session.query(model.App).get(1)
        app1.info = dict(tutorial="some help")
        model.Session.commit()
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
        app1 = model.Session.query(model.App).get(1)
        app1.info = dict(tutorial="some help")
        model.Session.commit()
        self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" in res.data,\
                "There should be some tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data

    def test_28_non_tutorial_signed_user(self):
        """Test WEB app without tutorial work as signed in user"""
        Fixtures.create()
        model.Session.commit()
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
        model.Session.commit()
        self.register()
        # First time accessing the app should redirect me to the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data,\
                "There should not be a tutorial for the application"
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/app/test-app/newtask', follow_redirects=True)
        assert "some help" not in res.data


    def test_30_app_id_owner(self):
        """Test WEB application page shows the ID to the owner"""
        self.register()
        self.new_application()

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sample App" in res.data, "Application should be shown to the owner"
        assert '<strong><i class="icon-cog"></i> ID</strong>: 1' in res.data,\
                "Application ID should be shown to the owner"


    def test_30_app_id_anonymous_user(self):
        """Test WEB application page does not  show the ID to anonymous users"""
        self.register()
        self.new_application()
        self.signout()

        res = self.app.get('/app/sampleapp', follow_redirects=True)
        assert "Sample App" in res.data, "Application name should be shown to users"
        assert '<strong><i class="icon-cog"></i> ID</strong>: 1' not in res.data,\
                "Application ID should be shown to the owner"

    def test_31_user_profile_progress(self):
        """Test WEB user progress profile page works"""
        self.register()
        self.new_application()
        app = model.Session.query(model.App).first()
        task = model.Task(app_id=app.id, info={'n_answers': '10'})
        model.Session.add(task)
        model.Session.commit()
        for i in range(10):
            task_run = model.TaskRun(app_id=app.id, task_id=1, user_id=1,
                                     info={'answer': 1})
            model.Session.add(task_run)
            model.Session.commit()
            self.app.get('api/app/%s/newtask' % app.id)

        res = self.app.get('account/profile', follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert "Contributed tasks: 10" in res.data, res.data
        assert "Contribute!" in res.data, "There should be a Contribute button"
