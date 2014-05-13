# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

import json
from helper import web
from default import db, with_context
from mock import patch
from collections import namedtuple
from bs4 import BeautifulSoup
from pybossa.model.user import User
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.category import Category


FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestAdmin(web.Helper):
    pkg_json_not_found = {
        "help": "Return ...",
        "success": False,
        "error": {
            "message": "Not found",
            "__type": "Not Found Error"}}
    # Tests

    @with_context
    def test_00_first_user_is_admin(self):
        """Test ADMIN First Created user is admin works"""
        self.register()
        user = db.session.query(User).get(1)
        assert user.admin == 1, "User ID:1 should be admin, but it is not"

    @with_context
    def test_01_admin_index(self):
        """Test ADMIN index page works"""
        self.register()
        res = self.app.get("/admin", follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "There should be an index page for admin users and apps"
        assert "Settings" in res.data, err_msg
        divs = ['featured-apps', 'users', 'categories', 'users-list']
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg

    @with_context
    def test_01_admin_index_anonymous(self):
        """Test ADMIN index page works as anonymous user"""
        res = self.app.get("/admin", follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

    @with_context
    def test_01_admin_index_authenticated(self):
        """Test ADMIN index page works as signed in user"""
        self.register()
        self.signout()
        self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app.get("/admin", follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg

    @with_context
    def test_02_second_user_is_not_admin(self):
        """Test ADMIN Second Created user is NOT admin works"""
        self.register()
        self.signout()
        self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
        self.signout()
        user = db.session.query(User).get(2)
        assert user.admin == 0, "User ID: 2 should not be admin, but it is"

    @with_context
    def test_03_admin_featured_apps_as_admin(self):
        """Test ADMIN featured apps works as an admin user"""
        self.register()
        self.signin()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Manage featured applications" in res.data, res.data

    @with_context
    def test_04_admin_featured_apps_as_anonymous(self):
        """Test ADMIN featured apps works as an anonymous user"""
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Please sign in to access this page" in res.data, res.data

    @with_context
    def test_05_admin_featured_apps_as_user(self):
        """Test ADMIN featured apps works as a signed in user"""
        self.register()
        self.signout()
        self.register()
        self.register(username="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert res.status == "403 FORBIDDEN", res.status

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_06_admin_featured_apps_add_remove_app(self, mock):
        """Test ADMIN featured apps add-remove works as an admin user"""
        self.register()
        self.new_application()
        self.update_application()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create an App" in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        # Only apps that have been published can be featured
        self.new_task(1)
        app = db.session.query(App).get(1)
        app.info = dict(task_presenter="something")
        db.session.add(app)
        db.session.commit()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Featured" in res.data, res.data
        assert "Sample App" in res.data, res.data
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
        # A retry should fail
        res = self.app.post('/admin/featured/1')
        err = json.loads(res.data)
        err_msg = "App.id 1 alreay in Featured table"
        assert err['error'] == err_msg, err_msg
        assert err['status_code'] == 415, "Status code should be 415"

        # Remove it again from the Featured list
        res = self.app.delete('/admin/featured/1')
        assert res.status == "204 NO CONTENT", res.status
        # Check that it is not listed in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Sample App" not in res.data,\
            "The application should not be listed in the front page"\
            " as it is not featured"
        # If we try to delete again, it should return an error
        res = self.app.delete('/admin/featured/1')
        err = json.loads(res.data)
        assert err['status_code'] == 404, "App should not be found"
        err_msg = 'App.id 1 is not in Featured table'
        assert err['error'] == err_msg, err_msg

        # Try with an id that does not exist
        res = self.app.delete('/admin/featured/999')
        err = json.loads(res.data)
        assert err['status_code'] == 404, "App should not be found"
        err_msg = 'App.id 999 not found'
        assert err['error'] == err_msg, err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_07_admin_featured_apps_add_remove_app_non_admin(self, mock):
        """Test ADMIN featured apps add-remove works as an non-admin user"""
        self.register()
        self.signout()
        self.register(username="John2", email="john2@john.com",
                      password="passwd")
        self.new_application()
        # The application is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        err_msg = ("The application should not be listed in the front page"
                   "as it is not featured")
        assert "Create an App" in res.data, err_msg
        res = self.app.get('/admin/featured', follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg
        # Try to add the app to the featured list
        res = self.app.post('/admin/featured/1')
        err_msg = ("The user should not be able to POST to this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg
        # Try to remove it again from the Featured list
        res = self.app.delete('/admin/featured/1')
        err_msg = ("The user should not be able to DELETE to this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_08_admin_featured_apps_add_remove_app_anonymous(self, mock):
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
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

        # Try to add the app to the featured list
        res = self.app.post('/admin/featured/1', follow_redirects=True)
        err_msg = ("The user should not be able to POST to this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

        # Try to remove it again from the Featured list
        res = self.app.delete('/admin/featured/1', follow_redirects=True)
        err_msg = ("The user should not be able to DELETE to this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in res.data, err_msg

    @with_context
    def test_09_admin_users_as_admin(self):
        """Test ADMIN users works as an admin user"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data

    @with_context
    def test_10_admin_user_not_listed(self):
        """Test ADMIN users does not list himself works"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data
        assert "Current Users with Admin privileges" not in res.data, res.data
        assert "John" not in res.data, res.data

    @with_context
    def test_11_admin_user_not_listed_in_search(self):
        """Test ADMIN users does not list himself in the search works"""
        self.register()
        data = {'user': 'john'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Manage Admin Users" in res.data, res.data
        assert "Current Users with Admin privileges" not in res.data, res.data
        assert "John" not in res.data, res.data

    @with_context
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
        assert "Juan Jose" in res.data, "username should be searchable"
        # Check with uppercase
        data = {'user': 'JUAN'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        err_msg = "username search should be case insensitive"
        assert "Juan Jose" in res.data, err_msg
        # Search fullname
        data = {'user': 'Jose'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Juan Jose" in res.data, "fullname should be searchable"
        # Check with uppercase
        data = {'user': 'JOsE'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        err_msg = "fullname search should be case insensitive"
        assert "Juan Jose" in res.data, err_msg
        # Warning should be issued for non-found users
        data = {'user': 'nothingExists'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        warning = ("We didn't find a user matching your query: <strong>%s</strong>" %
                   data['user'])
        err_msg = "A flash message should be returned for non-found users"
        assert warning in res.data, err_msg

    @with_context
    def test_13_admin_user_add_del(self):
        """Test ADMIN add/del user to admin group works"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # Signin with admin user
        self.signin()
        # Add user.id=1000 (it does not exist)
        res = self.app.get("/admin/users/add/1000", follow_redirects=True)
        err = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert err['error'] == "User not found", err
        assert err['status_code'] == 404, err


        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        assert "Current Users with Admin privileges" in res.data
        err_msg = "User.id=2 should be listed as an admin"
        assert "Juan Jose" in res.data, err_msg
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        assert "Current Users with Admin privileges" not in res.data
        err_msg = "User.id=2 should be listed as an admin"
        assert "Juan Jose" not in res.data, err_msg
        # Delete a non existant user should return an error
        res = self.app.get("/admin/users/del/5000", follow_redirects=True)
        err = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert err['error'] == "User.id not found", err
        assert err['status_code'] == 404, err

    @with_context
    def test_14_admin_user_add_del_anonymous(self):
        """Test ADMIN add/del user to admin group works as anonymous"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        err_msg = "User should be redirected to signin"
        assert "Please sign in to access this page" in res.data, err_msg
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        err_msg = "User should be redirected to signin"
        assert "Please sign in to access this page" in res.data, err_msg

    @with_context
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

    @with_context
    def test_16_admin_user_export(self):
        """Test ADMIN user list export works as admin"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", username="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin()
        # The user is redirected to '/admin/' if no format is specified
        res = self.app.get('/admin/users/export', follow_redirects=True)
        assert 'Featured Applications' in res.data, res.data
        assert 'Administrators' in res.data, res.data
        res = self.app.get('/admin/users/export?firmit=', follow_redirects=True)
        assert 'Featured Applications' in res.data, res.data
        assert 'Administrators' in res.data, res.data
        # A 415 error is raised if the format is not supported (is not either json or csv)
        res = self.app.get('/admin/users/export?format=bad',
                            follow_redirects=True)
        assert res.status_code == 415, res.status_code
        # JSON is a valid format for exports
        res = self.app.get('/admin/users/export?format=json',
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'application/json', res.mimetype
        #CSV is a valid format for exports
        res = self.app.get('/admin/users/export?format=csv',
                            follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'text/csv', res.mimetype

    @with_context
    def test_17_admin_user_export_anonymous(self):
        """Test ADMIN user list export works as anonymous user"""
        self.register()
        self.signout()

        # Whichever the args of the request are, the user is redirected to login
        res = self.app.get('/admin/users/export', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        res = self.app.get('/admin/users/export?firmit=', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        res = self.app.get('/admin/users/export?format=bad',
                            follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        res = self.app.get('/admin/users/export?format=json',
                            follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

    @with_context
    def test_18_admin_user_export_authenticated(self):
        """Test ADMIN user list export works as authenticated non-admin user"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", username="juan",
                      email="juan@juan.com", password="juan")

        # No matter what params in the request, Forbidden is raised
        res = self.app.get('/admin/users/export', follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?firmit=', follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?format=bad',
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?format=json',
                            follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_19_admin_update_app(self, Mock, Mock2):
        """Test ADMIN can update an app that belongs to another user"""
        html_request = FakeRequest(json.dumps(self.pkg_json_not_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
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

        app = db.session.query(App)\
                .filter_by(short_name="rootsampleapp").first()
        juan = db.session.query(User).filter_by(name="juan").first()
        assert app.owner_id == juan.id, "Owner_id should be: %s" % juan.id
        assert app.owner_id != 1, "The owner should be not updated"
        res = self.update_application(short_name="rootsampleapp",
                                      new_short_name="sampleapp",
                                      new_long_description="New Long Desc")
        res = self.app.get('/app/sampleapp', follow_redirects=True)
        err_msg = "The long description should have been updated"
        assert "New Long Desc" in res.data, err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_20_admin_delete_app(self, mock):
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
        err_msg = "The app should be deleted by admin users"
        assert "Application deleted!" in res.data, err_msg

    @with_context
    def test_21_admin_delete_tasks(self):
        """Test ADMIN can delete an app's tasks that belongs to another user"""
        # Admin
        self.create()
        tasks = db.session.query(Task).filter_by(app_id=1).all()
        assert len(tasks) > 0, "len(app.tasks) > 0"
        res = self.signin(email=u'root@root.com', password=u'tester' + 'root')
        res = self.app.get('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app.post('/app/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg
        tasks = db.session.query(Task).filter_by(app_id=1).all()
        assert len(tasks) == 0, "len(app.tasks) != 0"

    @with_context
    def test_22_admin_list_categories(self):
        """Test ADMIN list categories works"""
        self.create()
        # Anonymous user
        url = '/admin/categories'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        self.signout()

        # Admin user
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Admin users should be get a list of Categories"
        assert dom.find(id='categories') is not None, err_msg

    @with_context
    def test_23_admin_add_category(self):
        """Test ADMIN add category works"""
        self.create()
        category = {'name': 'cat', 'short_name': 'cat',
                    'description': 'description'}
        # Anonymous user
        url = '/admin/categories'
        res = self.app.post(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        self.signout()

        # Admin
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category should be added"
        assert "Category added" in res.data, err_msg
        assert category['name'] in res.data, err_msg

        category = {'name': 'cat', 'short_name': 'cat',
                    'description': 'description'}

        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category form validation should work"
        assert "Please correct the errors" in res.data, err_msg


    @with_context
    def test_24_admin_update_category(self):
        """Test ADMIN update category works"""
        self.create()
        obj = db.session.query(Category).get(1)
        _name = obj.name
        category = obj.dictize()

        # Anonymous user GET
        url = '/admin/categories/update/%s' % obj.id
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        # Anonymous user POST
        res = self.app.post(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin GET
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        # Authenticated user but not admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        self.signout()

        # Admin GET
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Category should be listed for admin user"
        assert _name in res.data, err_msg
        # Check 404
        url_404 = '/admin/categories/update/5000'
        res = self.app.get(url_404, follow_redirects=True)
        assert res.status_code == 404, res.status_code
        # Admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category should be updated"
        assert "Category updated" in res.data, err_msg
        assert category['name'] in res.data, err_msg
        updated_category = db.session.query(Category).get(obj.id)
        assert updated_category.name == obj.name, err_msg
        # With not valid form
        category['name'] = None
        res = self.app.post(url, data=category, follow_redirects=True)
        assert "Please correct the errors" in res.data, err_msg

    @with_context
    def test_25_admin_delete_category(self):
        """Test ADMIN delete category works"""
        self.create()
        obj = db.session.query(Category).get(2)
        category = obj.dictize()

        # Anonymous user GET
        url = '/admin/categories/del/%s' % obj.id
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        # Anonymous user POST
        res = self.app.post(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin GET
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        # Authenticated user but not admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        self.signout()

        # Admin GET
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Category should be listed for admin user"
        assert category['name'] in res.data, err_msg
        # Admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category should be deleted"
        assert "Category deleted" in res.data, err_msg
        assert category['name'] not in res.data, err_msg
        output = db.session.query(Category).get(obj.id)
        assert output is None, err_msg
        # Non existant category
        category['id'] = 5000
        url = '/admin/categories/del/5000'
        res = self.app.post(url, data=category, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # Now try to delete the only available Category
        obj = db.session.query(Category).first()
        url = '/admin/categories/del/%s' % obj.id
        category = obj.dictize()
        res = self.app.post(url, data=category, follow_redirects=True)
        print res.data
        err_msg = "Category should not be deleted"
        assert "Category deleted" not in res.data, err_msg
        assert category['name'] in res.data, err_msg
        output = db.session.query(Category).get(obj.id)
        assert output.id == category['id'], err_msg
