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

    def update_profile(self, method="POST", id=1, fullname="John Doe", name="johndoe", email_addr="johndoe@example.com"):
        """Helper function to update the profile of users"""
        if (method == "POST"):
            return self.app.post("/account/profile/update", data = {
                    'id': id,
                    'fullname': fullname,
                    'name': name,
                    'email_addr': email_addr
                }, follow_redirects = True)
        else:
            return self.app.get("/account/profile/update", follow_redirects = True)

    def logout(self):
        """Helper function to logout current user"""
        return self.app.get('/account/logout', follow_redirects = True)

    def new_application(self, method="POST", name="Sample App", short_name="sampleapp", description="Description", hidden = False):
        """Helper function to create an application"""
        if method == "POST":
            if hidden:
                return self.app.post("/app/new", data = {
                    'name': name,
                    'short_name': short_name,
                    'description': description,
                    'hidden': hidden,
                }, follow_redirects = True)
            else:
                return self.app.post("/app/new", data = {
                    'name': name,
                    'short_name': short_name,
                    'description': description
                }, follow_redirects = True)
        else:
            return self.app.get("/app/new", follow_redirects = True)

    def delete_application(self, method="POST", short_name="sampleapp"):
        """Helper function to create an application"""
        if method == "POST":
            return self.app.post("/app/%s/delete" % short_name, follow_redirects = True)
        else:
            return self.app.get("/app/%s/delete" % short_name, follow_redirects = True)

    def update_application(self, method="POST", short_name="sampleapp", id=1, new_name="Sample App", new_short_name="sampleapp", new_description="Description", new_hidden=False):
        """Helper function to create an application"""
        if method == "POST":
            if new_hidden:
                return self.app.post("/app/%s/update" % short_name, data = {
                        'id': id,
                        'name': new_name,
                        'short_name': new_short_name,
                        'description': new_description,
                        'hidden': new_hidden,
                    }, follow_redirects = True)
            else:
                return self.app.post("/app/%s/update" % short_name, data = {
                        'id': id,
                        'name': new_name,
                        'short_name': new_short_name,
                        'description': new_description,
                    }, follow_redirects = True)
        else:
            return self.app.get("/app/%s/update" % short_name, follow_redirects = True)

    # Tests
    def test_stats(self):
        """Test WEB leaderboard or stats page works"""
        res = self.app.get("/stats", follow_redirects = True)
        assert self.html_title("Leaderboard") in res.data, res
        assert "Most active applications" in res.data, res
        assert "Most active volunteers" in res.data, res

    def test_register(self):
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
        assert "Full name must be between 3 and 35 characters long" in res.data, res

        res = self.register(username='')
        assert self.html_title("Register") in res.data, res
        assert "User name must be between 3 and 35 characters long" in res.data, res

        res = self.register(email = '')
        assert self.html_title("Register") in res.data, res
        assert self.html_title("Register") in res.data, res
        assert "Email must be between 3 and 35 characters long" in res.data, res

        res = self.register(email = 'invalidemailaddress')
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
    
    def test_login_logout(self):
        """Test WEB logging in and logging out works"""
        res = self.register()
        # Log out as the registration already logs in the user
        res = self.logout()

        res = self.login(method="GET")
        assert self.html_title("Login") in res.data, res
        assert "Login" in res.data, res

        res = self.login(username='')
        assert "Please correct the errors" in  res.data, res
        assert "The username is required" in res.data, res

        res = self.login(password='')
        assert "Please correct the errors" in  res.data, res
        assert "You must provide a password" in res.data, res

        res = self.login(username='', password='')
        assert "Please correct the errors" in  res.data, res
        assert "The username is required" in res.data, res
        assert "You must provide a password" in res.data, res

        res = self.login(username='wrongusername')
        assert "Incorrect email/password" in  res.data, res

        res = self.login(password='wrongpassword')
        assert "Incorrect email/password" in  res.data, res

        res = self.login(username='wrongusername', password='wrongpassword')
        assert "Incorrect email/password" in  res.data, res

        res = self.login()
        assert self.html_title() in res.data, res
        assert "Welcome back John Doe" in res.data, res

        # Check profile page with several information chunks
        res = self.profile()
        assert self.html_title("Profile") in res.data, res
        assert "John Doe" in res.data, res
        assert "Logged in " in res.data, res
        assert "johndoe@example.com" in res.data, res
        assert "API key" in res.data, res
        assert "Create a new application" in res.data, res


        # Log out
        res = self.logout()
        assert self.html_title() in res.data, res
        assert "You are now logged out" in res.data, res
        
        # Request profile as an anonymous user
        res = self.profile()
        # As a user must be logged in to access, the page the title will be the redirection to log in
        assert self.html_title("Login") in res.data, res
        assert "Please log in to access this page." in res.data, res



        res = self.login(next='%2Faccount%2Fprofile')
        assert self.html_title("Profile") in res.data, res
        assert "Welcome back John Doe" in res.data, res
        assert "API key" in res.data, res

    def test_update_user_profile(self):
        """Test WEB update user profile"""

        # Create an account and log in
        self.register()

        # Update profile with new data
        res = self.update_profile(method="GET")
        assert self.html_title("Update your profile: John Doe") in res.data, res
        assert 'input id="id" name="id" type="hidden" value="1"' in res.data, res
        assert "John Doe" in res.data, res
        assert "Save the changes" in res.data, res

        res = self.update_profile(fullname="John Doe 2", email_addr="johndoe2@example.com")
        assert self.html_title("Profile") in res.data, res
        assert "Your profile has been updated!" in res.data, res
        assert "John Doe 2" in res.data, res
        assert "johndoe" in res.data, res
        assert "johndoe2@example.com" in res.data, res

        # Updating the username field forces the user to re-log in
        res = self.update_profile(fullname="John Doe 2", email_addr="johndoe2@example.com", name="johndoe2")
        assert "Your profile has been updated!" in res.data, res
        assert "Please log in to access this page" in res.data, res

        res = self.login(method="POST", username="johndoe2", password="p4ssw0rd", next="%2Faccount%2Fprofile")
        assert "Welcome back John Doe 2" in res.data, res
        assert "John Doe 2" in res.data, res
        assert "johndoe2" in res.data, res
        assert "johndoe2@example.com" in res.data, res

        res = self.logout()
        assert self.html_title() in res.data, res
        assert "You are now logged out" in res.data, res

        # A user must be logged in to access the update page, the page the title will be the redirection to log in
        res = self.update_profile(method="GET")
        assert self.html_title("Login") in res.data, res
        assert "Please log in to access this page." in res.data, res

        # A user must be logged in to access the update page, the page the title will be the redirection to log in
        res = self.update_profile()
        assert self.html_title("Login") in res.data, res
        assert "Please log in to access this page." in res.data, res



    def test_applications(self):
        """Test WEB applications index interface works"""
        self.register()
        self.new_application()
        self.logout()

        res = self.app.get('/app/' )
        assert self.html_title("Applications") in res.data, res
        assert "Available Projects" in res.data, res
        assert '/app/sampleapp' in res.data, res



    def test_get_application(self):
        """Test WEB application URL/<short_name> works"""
        # Login and create an application
        self.register()
        res = self.new_application()

        res = self.app.get('/app/sampleapp', follow_redirects = True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Description" in res.data, res
        assert "Completed tasks" in res.data, res
        assert "Edit the application" in res.data, res
        assert "Delete the application" in res.data, res
        self.logout()

        # Now as an anonymous user
        res = self.app.get('/app/sampleapp', follow_redirects = True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Description" in res.data, res
        assert "Completed tasks" in res.data, res
        assert "Edit the application" not in res.data, res
        assert "Delete the application" not in res.data, res

        # Now with a different user
        self.register(fullname="Perico Palotes", username="perico")
        res = self.app.get('/app/sampleapp', follow_redirects = True)
        assert self.html_title("Application: Sample App") in res.data, res
        assert "Description" in res.data, res
        assert "Completed tasks" in res.data, res
        assert "Edit the application" not in res.data, res
        assert "Delete the application" not in res.data, res


    def test_create_application(self):
        """Test WEB create an application works"""
        # Create an app as an anonymous user
        res = self.new_application(method="GET")
        assert self.html_title("Login") in res.data, res
        assert "Please log in to access this page" in res.data, res

        res = self.new_application()
        assert self.html_title("Login") in res.data, res
        assert "Please log in to access this page." in res.data, res

        # Login and create an application
        res = self.register()

        res = self.new_application(method="GET")
        assert self.html_title("New Application") in res.data, res
        assert "Create the application" in res.data, res

        res = self.new_application()
        assert self.html_title("Application: %s" % "Sample App" ) in res.data, res
        assert "Application created!" in res.data, res

    def test_update_application(self):
        """Test WEB update application works"""
        self.register()
        self.new_application()

        # Get the Update App web page
        res = self.update_application(method="GET")
        assert self.html_title("Update the application: Sample App") in res.data, res
        assert 'input id="id" name="id" type="hidden" value="1"' in res.data, res
        assert "Save the changes" in res.data, res

        # Update the application
        res = self.update_application(new_name="New Sample App", new_short_name="newshortname", new_description="New description", new_hidden=True)
        assert self.html_title("Application: New Sample App") in res.data, res
        assert "Application updated!" in res.data, res

    def test_hidden_applications(self):
        """Test WEB hidden application works"""
        self.register()
        self.new_application()
        self.update_application(new_hidden = True)
        self.logout()

        res = self.app.get('/app/',follow_redirects = True)
        assert "Sample App" not in res.data, res

        res = self.app.get('/app/sampleapp', follow_redirects = True)
        assert "Sorry! This app does not exists." in res.data, res
        
    def test_delete_application(self):
        """Test WEB delete application works"""
        self.register()
        self.new_application()
        res = self.delete_application(method="GET")
        assert self.html_title("Delete Application: Sample App") in res.data, res
        assert "No, do not delete it" in res.data, res

        res = self.delete_application()
        assert "Application deleted!" in res.data, res

