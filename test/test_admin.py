import json
from base import web, model, Fixtures


class TestAdmin:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        #Fixtures.create()

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
                    'long_description': long_description
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

    def test_01_first_user_is_admin(self):
        """Test ADMIN First Created user is admin works"""
        self.register()
        user = model.Session.query(model.User)\
                .get(1)
        assert user.admin == 1, "User ID:1 should be admin, but it is not"

    def test_02_second_user_is_not_admin(self):
        """Test ADMIN Second Created user is NOT admin works"""
        self.register()
        self.signout()
        self.register(username="tester2",
                email="tester2@tester.com", password="tester")
        self.signout()
        user = model.Session.query(model.User)\
                .get(2)
        assert user.admin == 0, "User ID: 2 should not be admin, but it is"

    def test_03_admin_featured_apps_as_admin(self):
        """Test ADMIN featured apps works ad an admin user"""
        self.register()
        self.signin()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Manage Featured applications" in res.data, res.data

    def test_04_admin_featured_apps_as_anonymous(self):
        """Test ADMIN featured apps works as an anonymous user"""
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Please sign in to access this page" in res.data, res.data

    def test_05_admin_featured_apps_as_user(self):
        """Test ADMIN featured apps works as a signed in user"""
        self.register()
        self.signout()
        self.register()
        self.register(username="tester2",
                email="tester2@tester.com", password="tester")
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert res.status == "403 FORBIDDEN", res.status

    def test_06_admin_featured_apps_add_app(self):
        """Test ADMIN featured apps add works as an admin user"""
        self.register()
        self.new_application()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create your own application!" in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Sample App" in res.data, res.data
        assert "Featured" in res.data, res.data
        # Add it to the Featured list
        res = self.app.post('/admin/featured/1')
        f = json.loads(res.data)
        assert f['id'] == 1, f
        assert f['app_id'] == 1, f
        # Check that it is listed in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Sample App" in res.data,\
            "The application should be listed in the front page"\
            " as it is featured"
        # Remove it again from the Featured list
        res = self.app.delete('/admin/featured/1')
        assert res.status == "204 NO CONTENT", res.status
        # Check that it is not listed in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Sample App" not in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
