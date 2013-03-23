import json
from base import web, model, Fixtures, db


class TestAdmin:
    def setUp(self):
        self.app = web.app.test_client()
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

    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next != None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data={
                    'email': email,
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
                    'allow_anonymous_contributors': allow_anonymous_contributors,
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

    def test_00_first_user_is_admin(self):
        """Test ADMIN First Created user is admin works"""
        self.register()
        user = db.session.query(model.User)\
                .get(1)
        assert user.admin == 1, "User ID:1 should be admin, but it is not"

    def test_01_admin_index(self):
        """Test ADMIN index page works"""
        self.register()
        res = self.app.get("/admin", follow_redirects=True)
        assert "Settings" in res.data,\
                "There should be an index page for admin users and apps"
        assert "Manage featured applications" in res.data,\
                "There should be a button for managing apps"
        assert "Manage admin users" in res.data,\
                "There should be a button for managing users"

    def test_01_admin_index_anonymous(self):
        """Test ADMIN index page works as anonymous user"""
        res = self.app.get("/admin", follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "The user should not be able to access this page"\
                " but the returned status is %s" % res.data

    def test_01_admin_index_authenticated(self):
        """Test ADMIN index page works as signed in user"""
        self.register()
        self.signout()
        self.register(username="tester2",
                email="tester2@tester.com", password="tester")
        res = self.app.get("/admin", follow_redirects=True)
        assert "403 FORBIDDEN" in res.status,\
                "The user should not be able to access this page"\
                " but the returned status is %s" % res.status

    def test_02_second_user_is_not_admin(self):
        """Test ADMIN Second Created user is NOT admin works"""
        self.register()
        self.signout()
        self.register(username="tester2",
                email="tester2@tester.com", password="tester")
        self.signout()
        user = db.session.query(model.User)\
                .get(2)
        assert user.admin == 0, "User ID: 2 should not be admin, but it is"

    def test_03_admin_featured_apps_as_admin(self):
        """Test ADMIN featured apps works as an admin user"""
        self.register()
        self.signin()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Manage featured applications" in res.data, res.data

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

    def test_06_admin_featured_apps_add_remove_app(self):
        """Test ADMIN featured apps add-remove works as an admin user"""
        self.register()
        self.new_application()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create an App" in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        # Only apps that have been published can be featured
        self.new_task(1)
        app = db.session.query(model.App).get(1)
        app.info = dict(task_presenter="something")
        db.session.add(app)
        db.session.commit()
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

    def test_07_admin_featured_apps_add_remove_app_non_admin(self):
        """Test ADMIN featured apps add-remove works as an non-admin user"""
        self.register()
        self.signout()
        self.register(username="John2", email="john2@john.com",
                password="passwd")
        self.new_application()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create an App" in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "403 FORBIDDEN" in res.status,\
                "The user should not be able to access this page"\
                " but the returned status is %s" % res.status
        # Try to add the app to the featured list
        res = self.app.post('/admin/featured/1')
        assert "403 FORBIDDEN" in res.status,\
                "The user should not be able to POST to this page"\
                " but the returned status is %s" % res.status
        # Try to remove it again from the Featured list
        res = self.app.delete('/admin/featured/1')
        assert "403 FORBIDDEN" in res.status,\
                "The user should not be able to DELETE to this page"\
                " but the returned status is %s" % res.status

    def test_08_admin_featured_apps_add_remove_app_anonymous(self):
        """Test ADMIN featured apps add-remove works as an anonymous user"""
        self.register()
        self.new_application()
        self.signout()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create an App" in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "The user should not be able to access this page"\
                " but the returned status is %s" % res.data
        # Try to add the app to the featured list
        res = self.app.post('/admin/featured/1', follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "The user should not be able to POST to this page"\
                " but the returned status is %s" % res.data
        # Try to remove it again from the Featured list
        res = self.app.delete('/admin/featured/1', follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "The user should not be able to DELETE to this page"\
                " but the returned status is %s" % res.data

    def test_09_admin_users_as_admin(self):
        """Test ADMIN users works as an admin user"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data

    def test_10_admin_user_not_listed(self):
        """Test ADMIN users does not list himself works"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data
        assert "Current Users with Admin privileges" not in res.data, res.data
        assert "John" not in res.data, res.data

    def test_11_admin_user_not_listed_in_search(self):
        """Test ADMIN users does not list himself in the search works"""
        self.register()
        data = {'user': 'john'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data
        assert "Current Users with Admin privileges" not in res.data, res.data
        assert "John" not in res.data, res.data

    def test_12_admin_user_search(self):
        """Test ADMIN users search works"""
        # Create two users
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.signout()
        # Signin with admin user
        self.signin()
        data = {'user': 'juan'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        print res.data
        assert "Juan Jose" in res.data, "username should be searchable"
        # Check with uppercase
        data = {'user': 'JUAN'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Juan Jose" in res.data,\
                "username search should be case insensitive"
        # Search fullname
        data = {'user': 'Jose'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Juan Jose" in res.data, "fullname should be searchable"
        # Check with uppercase
        data = {'user': 'JOsE'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Juan Jose" in res.data,\
                "fullname search should be case insensitive"
        # Warning should be issued for non-found users
        data = {'user': 'nothingExists'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        warning = "We didn't find a user matching your query: <strong>"\
                + data['user'] + "</strong>"
        assert warning in res.data,\
                "A flash message should be returned for non-found users"

    def test_13_admin_user_add_del(self):
        """Test ADMIN add/del user to admin group works"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.signout()
        # Signin with admin user
        self.signin()
        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        assert "Current Users with Admin privileges" in res.data
        assert "Juan Jose" in res.data,\
                "User.id=2 should be listed as an admin"
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        assert "Current Users with Admin privileges" not in res.data
        assert "Juan Jose" not in res.data,\
                "User.id=2 should be listed as an admin"

    def test_14_admin_user_add_del_anonymous(self):
        """Test ADMIN add/del user to admin group works as anonymous"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.signout()
        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "User should be redirected to signin"
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        assert "Please sign in to access this page" in res.data,\
                "User should be redirected to signin"

    def test_15_admin_user_add_del_authenticated(self):
        """Test ADMIN add/del user to admin group works as authenticated"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", username="juan2",
                email="juan2@juan.com", password="juan2")
        self.signout()
        self.signin(email="juan2@juan.com", password="juan2")
        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        assert res.status == "403 FORBIDDEN",\
            "This action should be forbidden, not enought privileges"
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        assert res.status == "403 FORBIDDEN",\
            "This action should be forbidden, not enought privileges"

    def test_16_admin_update_app(self):
        """Test ADMIN can update an app that belongs to another user"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.new_application()
        self.signout()
        # Sign in with the root user
        self.signin()
        res = self.app.get('/app/sampleapp/settings')
        err_msg = "Admin users should be able to get the settings page for any app"
        assert res.status == "200 OK", err_msg
        res = self.update_application(method="GET")
        assert "Update the application" in res.data,\
            "The app should be updated by admin users"
        res = self.update_application(new_name="Root",
                new_short_name="rootsampleapp")
        res = self.app.get('/app/rootsampleapp', follow_redirects=True)
        assert "Root" in res.data, "The app should be updated by admin users"

        app = db.session.query(model.App)\
                .filter_by(short_name="rootsampleapp").first()
        juan = db.session.query(model.User).filter_by(name="juan").first()
        assert app.owner_id == juan.id, "Owner_id should be: %s" % juan.id
        assert app.owner_id != 1, "The owner should be not updated"

    def test_17_admin_delete_app(self):
        """Test ADMIN can delete an app that belongs to another user"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                email="juan@juan.com", password="juan")
        self.new_application()
        self.signout()
        # Sign in with the root user
        self.signin()
        res = self.delete_application(method="GET")
        assert "Yes, delete it" in res.data,\
            "The app should be deleted by admin users"
        res = self.delete_application()
        assert "Application deleted!" in res.data,\
                "The app should be deleted by admin users"

    def test_18_admin_delete_tasks(self):
        """Test ADMIN can delete an app's tasks that belongs to another user"""
        # Admin
        Fixtures.create()
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        assert len(tasks) > 0, "len(app.tasks) > 0"
        res = self.signin(email=u'root@root.com', password=u'tester' + 'root')
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg
        tasks = db.session.query(model.Task).filter_by(app_id=1).all()
        assert len(tasks) == 0, "len(app.tasks) != 0"
