import json

from flask import Flask, request
from flaskext.login import login_user, logout_user, current_user

from base import web, model, Fixtures
from nose.tools import assert_equal


class TestWeb:
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

    def register(self, method="POST", fullname="John Doe", username="johndoe", password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and login a user"""
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

    def login(self, method="POST", username="johndoe", password="p4ssw0rd", next=None):
        """Helper function to login current user"""
        url = '/account/login'
        if next != None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url, data =  {
                    'username': username,
                    'password': password,
                    }, follow_redirects = True)
        else:
            return self.app.get(url, follow_redirects = True)

    def profile(self):
        """Helper function to check profile of logged user"""
        return self.app.get("/account/profile", follow_redirects = True)

    def logout(self):
        """Helper function to logout current user"""
        return self.app.get('/account/logout', follow_redirects = True)

    def new_application(self, method="POST", name="Sample App", short_name="sampleapp", description="Description", hidden=0):
        """Helper function to create an application"""
        if method == "POST":
            return self.app.post("/app/new", data = {
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'hidden': hidden,
                }, follow_redirects = True)
        else:
            return self.app.get("/app/new", follow_redirects = True)

    def delete_application(self, method="POST", short_name="sampleapp"):
        """Helper function to create an application"""
        if method == "POST":
            return self.app.post("/app/%s/delete" % short_name, follow_redirects = True)
        else:
            return self.app.get("/app/%s/delete" % short_name, follow_redirects = True)

    def update_application(self, method="POST", short_name="sampleapp", id=1, new_name="Sample App", new_short_name="sampleapp", new_description="Description", new_hidden=0):
        """Helper function to create an application"""
        if method == "POST":
            return self.app.post("/app/%s/update" % short_name, data = {
                    'id': id,
                    'name': new_name,
                    'short_name': new_short_name,
                    'description': new_description,
                    'hidden': new_hidden,
                }, follow_redirects = True)
        else:
            return self.app.get("/app/%s/update" % short_name, follow_redirects = True)

    # Tests
    def test_stats(self):
        """Make sure the leaderboard or stats page works"""
        res = self.app.get("/stats", follow_redirects = True)
        assert self.html_title("Leaderboard") in res.data
        assert "Most active applications" in res.data
        assert "Most active volunteers" in res.data

    def test_register(self):
        """Make sure user registering works"""
        res = self.register(method="GET")
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert self.html_title("Register") in res.data

        res = self.register()
        assert self.html_title() in res.data
        assert "Thanks for signing-up" in res.data

        res = self.register()
        #print res.data
        assert self.html_title("Register") in res.data
        assert "The user name is already taken" in res.data

        res = self.register(fullname='')
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Full name must be between 3 and 35 characters long" in res.data

        res = self.register(username='')
        #print res.data
        assert self.html_title("Register") in res.data
        assert "User name must be between 3 and 35 characters long" in res.data

        res = self.register(email = '')
        assert self.html_title("Register") in res.data
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Email must be between 3 and 35 characters long" in res.data

        res = self.register(email = 'invalidemailaddress')
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Invalid email address" in res.data

        res = self.register()
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Email is already taken" in res.data

        res = self.register(password='')
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Password cannot be empty" in res.data

        res = self.register(password2='different')
        #print res.data
        assert self.html_title("Register") in res.data
        assert "Passwords must match" in res.data
    
    def test_login_logout(self):
        """Make sure logging in and logging out works"""
        res = self.register()
        # Log out as the registration already logs in the user
        res = self.logout()

        res = self.login(method="GET")
        assert self.html_title("Login") in res.data
        assert "Login" in res.data

        res = self.login()
        assert self.html_title() in res.data
        assert "Welcome back John Doe" in res.data

        # Check profile page with several information chunks
        res = self.profile()
        assert self.html_title("Profile") in res.data
        assert "John Doe" in res.data
        assert "johndoe@example.com" in res.data
        assert "API key" in res.data
        assert "Create a new application" in res.data

        # Log out
        res = self.logout()
        #print res.data
        assert self.html_title() in res.data
        assert "You are now logged out" in res.data
        
        # Request profile as an anonymous user
        res = self.profile()
        #print res.data
        # As a user must be logged in to access, the page the title will be the redirection to log in
        assert self.html_title("Login") in res.data
        assert "Please log in to access this page." in res.data

        res = self.login(next='%2Faccount%2Fprofile')
        #print res
        assert self.html_title("Profile") in res.data
        assert "Welcome back John Doe" in res.data
        assert "API key" in res.data

    def test_applications(self):
        """Make sure applications web interface works"""
        res = self.app.get('/app/')
        assert self.html_title("Applications") in res.data
        assert "Available Projects" in res.data

    def test_create_application(self):
        """Make sure create an application works"""
        # Create an app as an anonymous user
        res = self.new_application(method="GET")
        assert self.html_title("Login") in res.data
        assert "Please log in to access this page" in res.data

        res = self.new_application()
        #print res.data
        assert self.html_title("Login") in res.data
        assert "Please log in to access this page." in res.data

        # Login and create an application
        res = self.register()

        res = self.new_application(method="GET")
        assert self.html_title("New Application") in res.data
        assert "Create the application" in res.data

        res = self.new_application()
        #print res.data
        assert self.html_title("Application: %s" % "Sample App" ) in res.data
        assert "Application created!" in res.data

    def test_update_application(self):
        """Make sure update an application works"""
        self.register()
        self.new_application()

        # Get the Update App web page
        res = self.update_application(method="GET")
        print res.data
        assert self.html_title("Update the application: Sample App") in res.data
        assert '<input id="id" name="id" type="hidden" value="1" />' in res.data
        assert "Save the changes" in res.data

        # Update the application
        res = self.update_application(new_name="New Sample App", new_short_name="newshortname", new_description="New description", new_hidden=1)
        print res.data
        assert self.html_title("Application: New Sample App") in res.data
        assert "Application updated!" in res.data
        
    def test_delete_application(self):
        """Make sure deleting an application works"""
        self.register()
        self.new_application()
        res = self.delete_application(method="GET")
        assert self.html_title("Delete Application: Sample App") in res.data
        assert "No, do not delete it" in res.data

        res = self.delete_application()
        assert "Application deleted!" in res.data

