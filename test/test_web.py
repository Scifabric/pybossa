import json

from flask import Flask, request
from flaskext.login import login_user, logout_user, current_user

from base import web, model, Fixtures
from nose.tools import assert_equal


class TestWebAccounts:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Helper functions
    def register(self, fullname, username, password, password2=None, email=None):
        """Helper function to register and login a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        return self.app.post('/account/register', data = {
            'fullname': fullname,
            'username': username,
            'email_addr': email,
            'password': password,
            'confirm': password2,
            }, follow_redirects = True)

    def login(self, username, password, next=None):
        """Helper function to login current user"""
        url = '/account/login'
        if next != None:
            url = url + '?next=' + next
        return self.app.post(url, data =  {
                'username': username,
                'password': password,
                }, follow_redirects = True)

    def profile(self):
        """Helper function to check profile of logged user"""
        return self.app.get("/account/profile", follow_redirects = True)

    def logout(self):
        """Helper function to logout current user"""
        return self.app.get('/account/logout', follow_redirects = True)

    # Tests
    def test_register(self):
        """Make sure registering works"""
        res = self.register('John Doe', 'johndoe', 'p4ssw0rd')
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert "Thanks for signing-up" in res.data

        res = self.register('John Doe', 'johndoe', 'p4ssw0rd')
        print res.data
        assert "The user name is already taken" in res.data

        res = self.register('', 'johndoe', 'p4ssw0rd')
        print res.data
        assert "Full name must be between 3 and 35 characters long" in res.data

        res = self.register('John Doe', '', 'p4ssw0rd')
        print res.data
        assert "User name must be between 3 and 35 characters long" in res.data

        res = self.register('John Doe', 'johndoe', 'p4ssw0rd', email = '')
        print res.data
        assert "Email must be between 3 and 35 characters long" in res.data

        res = self.register('John Doe', 'johndoe', 'p4ssw0rd', email = 'invalidemailaddress')
        print res.data
        assert "Invalid email address" in res.data

        res = self.register('John Doe', 'johndoe', 'p4ssw0rd')
        print res.data
        assert "Email is already taken" in res.data

        res = self.register('John Doe', 'johndoe', '')
        print res.data
        assert "Password cannot be empty" in res.data

        res = self.register('John Doe', 'johndoe', 'p4ssw0rd', password2='different')
        print res.data
        assert "Passwords must match" in res.data
    
    def test_login_logout(self):
        """Make sure logging in and logging out works"""
        res = self.register('John Doe', 'johndoe', 'password')
        # Log out as the registration already logs in the user
        res = self.logout()

        res = self.login('johndoe', 'password')
        assert "Welcome back John Doe" in res.data

        # Check profile page with several information chunks
        res = self.profile()
        assert "John Doe" in res.data
        assert "johndoe@example.com" in res.data
        assert "API key" in res.data
        assert "Create a new application" in res.data

        # Log out
        res = self.logout()
        print res.data
        assert "You are now logged out" in res.data
        
        # Request profile as an anonymous user
        res = self.profile()
        print res.data
        assert "Please log in to access this page." in res.data

        res = self.login('johndoe', 'password', next='%2Faccount%2Fprofile')
        print res
        assert "Welcome back John Doe" in res.data
        assert "API key" in res.data
