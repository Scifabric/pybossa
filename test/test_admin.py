# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import json
from helper import web
from default import db, with_context
from mock import patch
from collections import namedtuple
from bs4 import BeautifulSoup
from pybossa.model.user import User
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.category import Category
from pybossa.repositories import AnnouncementRepository
from pybossa.repositories import UserRepository
from factories import AnnouncementFactory
announcement_repo = AnnouncementRepository(db)
user_repo = UserRepository(db)


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
    @patch('pybossa.view.admin.sentinel.master.delete')
    def test_01_admin_index(self, sentinel_mock):
        """Test ADMIN index page works"""
        self.register()
        res = self.app.get("/admin", follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "There should be an index page for admin users and projects"
        assert "Settings" in str(res.data), err_msg
        divs = ['featured-apps', 'users', 'categories', 'users-list']
        for div in divs:
            err_msg = "There should be a button for managing %s" % div
            assert dom.find(id=div) is not None, err_msg
        key = "notify:admin:1"
        sentinel_mock.assert_called_with(key)

    @with_context
    @patch('pybossa.view.admin.sentinel.master.delete')
    def test_01_admin_index_json(self, sentinel_mock):
        """Test ADMIN JSON index page works"""
        self.register()
        res = self.app_get_json("/admin/")
        data = json.loads(res.data)
        err_msg = "There should be an index page for admin users and projects"
        assert data.get('template') == '/admin/index.html'
        key = "notify:admin:1"
        sentinel_mock.assert_called_with(key)


    @with_context
    def test_01_admin_index_anonymous(self):
        """Test ADMIN index page works as anonymous user"""
        res = self.app.get("/admin", follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in str(res.data), err_msg

    @with_context
    def test_01_admin_index_anonymous_json(self):
        """Test ADMIN JSON index page works as anonymous user"""
        res = self.app_get_json("/admin/", follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in str(res.data), err_msg


    @with_context
    def test_01_admin_index_authenticated(self):
        """Test ADMIN index page works as signed in user"""
        self.register()
        self.signout()
        self.register(name="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app.get("/admin", follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg

    @with_context
    def test_01_admin_index_authenticated_json(self):
        """Test ADMIN JSON index page works as signed in user"""
        self.register()
        self.signout()
        self.register(name="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app_get_json("/admin/")
        data = json.loads(res.data)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg
        assert data.get('code') == 403, err_msg


    @with_context
    def test_02_second_user_is_not_admin(self):
        """Test ADMIN Second Created user is NOT admin works"""
        self.register()
        self.signout()
        self.register(name="tester2", email="tester2@tester.com",
                      password="tester")
        self.signout()
        user = db.session.query(User).get(2)
        assert user.admin == 0, "User ID: 2 should not be admin, but it is"

    @with_context
    def test_03_admin_featured_apps_as_admin(self):
        """Test ADMIN featured projects works as an admin user"""
        self.register()
        self.signin()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Manage featured projects" in str(res.data), res.data

    @with_context
    def test_03_2_admin_featured_apps_as_admin_json(self):
        """Test ADMIN featured projects works as an admin user json"""
        self.register()
        self.signin()
        res = self.app_get_json('/admin/featured')
        data = json.loads(res.data)
        assert 'categories' in data, data
        assert 'projects' in data, data
        err_msg = 'template wrong'
        assert data['template'] == '/admin/projects.html', err_msg
        assert 'form' in data, data
        assert 'csrf' in data['form'], data

    @with_context
    def test_04_admin_featured_apps_as_anonymous(self):
        """Test ADMIN featured projects works as an anonymous user"""
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Please sign in to access this page" in str(res.data), res.data

    @with_context
    def test_04_2_admin_featured_apps_as_anonymous_json(self):
        """Test ADMIN featured projects works as an anonymous user json"""
        res = self.app_get_json('/admin/featured')
        assert res.status_code == 302, res.status_code
        err_msg = 'private information leaked'
        assert 'categories' not in str(res.data), err_msg
        assert 'projects' not in str(res.data), err_msg

    @with_context
    def test_05_admin_featured_apps_as_user(self):
        """Test ADMIN featured projects works as a signed in user"""
        self.register()
        self.signout()
        self.register(name="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert res.status == "403 FORBIDDEN", res.status

    @with_context
    def test_05_2_admin_featured_apps_as_user_json(self):
        """Test ADMIN featured projects works as a signed in user json"""
        self.register()
        self.signout()
        self.register(name="tester2", email="tester2@tester.com",
                      password="tester")
        res = self.app_get_json('/admin/featured')
        assert res.status == "403 FORBIDDEN", res.status
        err_msg = 'private information leaked'
        assert 'categories' not in str(res.data), err_msg
        assert 'projects' not in str(res.data), err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    @patch('pybossa.forms.validator.requests.get')
    def test_06_admin_featured_apps_add_remove_app(self, mock, mock_webhook):
        """Test ADMIN featured projects add-remove works as an admin user"""
        html_request = FakeRequest(json.dumps(self.pkg_json_not_found), 200,
                                   {'content-type': 'application/json'})
        mock_webhook.return_value = html_request

        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        print(project)
        project.published = True
        db.session.commit()
        self.update_project()

        # The project is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Sample Project" not in str(res.data),\
            "The project should not be listed in the front page"\
            " as it is not featured"
        # Only projects that have been published can be featured
        self.new_task(1)
        project = db.session.query(Project).get(1)
        project.info = dict(task_presenter="something")
        db.session.add(project)
        db.session.commit()
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Featured" in str(res.data), res.data
        assert "Sample Project" in str(res.data), res.data


        # Add it to the Featured list
        res = self.app.post('/admin/featured/1')
        f = json.loads(res.data)
        assert f['id'] == 1, f
        assert f['featured'] is True, f
        # Check can be removed from featured
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Remove from Featured" in str(res.data),\
            "The project should have a button to remove from featured"
        # A retry should fail
        res = self.app.post('/admin/featured/1')
        err = json.loads(res.data)
        err_msg = "Project.id 1 already featured"
        assert err['error'] == err_msg, err_msg
        assert err['status_code'] == 415, "Status code should be 415"

        # Remove it again from the Featured list
        res = self.app.delete('/admin/featured/1')
        f = json.loads(res.data)
        assert f['id'] == 1, f
        assert f['featured'] is False, f
        # Check that can be added to featured
        res = self.app.get('/admin/featured', follow_redirects=True)
        assert "Add to Featured" in str(res.data),\
            "The project should have a button to add to featured"
        # If we try to delete again, it should return an error
        res = self.app.delete('/admin/featured/1')
        err = json.loads(res.data)
        assert err['status_code'] == 415, "Project should not be found"
        err_msg = 'Project.id 1 is not featured'
        assert err['error'] == err_msg, err_msg

        # Try with an id that does not exist
        res = self.app.delete('/admin/featured/999')
        err = json.loads(res.data)
        assert err['status_code'] == 404, "Project should not be found"
        err_msg = 'Project.id 999 not found'
        assert err['error'] == err_msg, err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_07_admin_featured_apps_add_remove_app_non_admin(self, mock):
        """Test ADMIN featured projects add-remove works as an non-admin user"""
        self.register()
        self.signout()
        self.register(name="John2", email="john2@john.com",
                      password="passwd")
        self.new_project()
        # The project is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        err_msg = ("The project should not be listed in the front page"
                   "as it is not featured")
        assert "Create" in str(res.data), err_msg
        res = self.app.get('/admin/featured', follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.status)
        assert "403 FORBIDDEN" in res.status, err_msg
        # Try to add the project to the featured list
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
        """Test ADMIN featured projects add-remove works as an anonymous user"""
        self.register()
        self.new_project()
        self.signout()
        # The project is in the system but not in the front page
        res = self.app.get('/', follow_redirects=True)
        assert "Create" in str(res.data),\
            "The project should not be listed in the front page"\
            " as it is not featured"
        res = self.app.get('/admin/featured', follow_redirects=True)
        err_msg = ("The user should not be able to access this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in str(res.data), err_msg

        # Try to add the project to the featured list
        res = self.app.post('/admin/featured/1', follow_redirects=True)
        err_msg = ("The user should not be able to POST to this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in str(res.data), err_msg

        # Try to remove it again from the Featured list
        res = self.app.delete('/admin/featured/1', follow_redirects=True)
        err_msg = ("The user should not be able to DELETE to this page"
                   " but the returned status is %s" % res.data)
        assert "Please sign in to access this page" in str(res.data), err_msg

    @with_context
    def test_09_admin_users_as_admin(self):
        """Test ADMIN users works as an admin user"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in str(res.data), res.data

    @with_context
    def test_09_admin_users_as_admin_json(self):
        """Test ADMIN JSON users works as an admin user"""
        self.register()
        res = self.app_get_json('/admin/users')
        data = json.loads(res.data)
        assert data.get('form') is not None, data
        assert data.get('form').get('csrf') is not None, data
        # See next test
        assert data.get('users') == [], data
        assert data.get('found') == [], data


    @with_context
    def test_10_admin_user_not_listed(self):
        """Test ADMIN users does not list himself works"""
        self.register()
        res = self.app.get('/admin/users', follow_redirects=True)
        assert "Manage Admin Users" in str(res.data), res.data
        assert "Current Users with Admin privileges" not in str(res.data), res.data
        assert "John" not in str(res.data), res.data

    @with_context
    def test_11_admin_user_not_listed_in_search(self):
        """Test ADMIN users does not list himself in the search works"""
        self.register()
        data = {'user': 'john'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "Manage Admin Users" in str(res.data), res.data
        assert "Current Users with Admin privileges" not in str(res.data), res.data
        assert "John" not in str(res.data), res.data

    @with_context
    def test_11_admin_user_not_listed_in_search_json(self):
        """Test ADMIN JSON users does not list himself in the search works"""
        self.register()
        data = {'user': 'john'}
        res = self.app_post_json('/admin/users', data=data)
        dat = json.loads(res.data)
        assert dat.get('found') == [], dat


    @with_context
    def test_12_admin_user_search_json(self):
        """test ADMIN JSON users search works"""
        # create two users
        self.register()
        self.signout()
        self.register(fullname="juan jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # signin with admin user
        self.signin()
        data = {'user': 'juan'}
        res = self.app_post_json('/admin/users', data=data)
        dat = json.loads(res.data)
        assert len(dat.get('found')) == 1, dat
        assert "juan jose" in dat.get('found')[0].get('fullname'), "username should be searchable"
        # check with uppercase
        data = {'user': 'juan'}
        res = self.app_post_json('/admin/users', data=data)
        err_msg = "username search should be case insensitive"
        dat = json.loads(res.data)
        assert len(dat.get('found')) == 1, dat
        assert "juan jose" in dat.get('found')[0].get('fullname'), err_msg
        # search fullname
        data = {'user': 'jose'}
        res = self.app_post_json('/admin/users', data=data)
        dat = json.loads(res.data)
        assert len(dat.get('found')) == 1, dat
        assert "juan jose" in dat.get('found')[0].get('fullname'), "fullname should be searchable"
        # check with uppercase
        data = {'user': 'jose'}
        res = self.app_post_json('/admin/users', data=data)
        dat = json.loads(res.data)
        assert len(dat.get('found')) == 1, dat
        err_msg = "fullname search should be case insensitive"
        assert "juan jose" in dat.get('found')[0].get('fullname'), err_msg
        # warning should be issued for non-found users
        data = {'user': 'nothingexists'}
        res = self.app_post_json('/admin/users', data=data)
        warning = ("We didn&#39;t find")
        err_msg = "a flash message should be returned for non-found users"
        dat = json.loads(res.data)
        assert warning in dat.get('flash'), (err_msg, dat)
        assert dat.get('status') == 'message', dat



    @with_context
    def test_12_admin_user_search(self):
        """test admin users search works"""
        # create two users
        self.register()
        self.signout()
        self.register(fullname="juan jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # signin with admin user
        self.signin()
        data = {'user': 'juan'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        print(res.data)
        assert "juan jose" in str(res.data), "username should be searchable"
        # check with uppercase
        data = {'user': 'juan'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        err_msg = "username search should be case insensitive"
        assert "juan jose" in str(res.data), err_msg
        # search fullname
        data = {'user': 'jose'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        assert "juan jose" in str(res.data), "fullname should be searchable"
        # check with uppercase
        data = {'user': 'jose'}
        res = self.app.post('/admin/users', data=data, follow_redirects=True)
        err_msg = "fullname search should be case insensitive"
        assert "juan jose" in str(res.data), err_msg
        # warning should be issued for non-found users
        # TODO: Update theme to use pybossaNotify and test this.
        # TODO: This however is tested in the json endpoint.
        # data = {'user': 'nothingexists'}
        # res = self.app.post('/admin/users', data=data, follow_redirects=True)
        # warning = ("We didn't find a user matching your query: <strong>%s</strong>" %
        #            data['user'])
        # err_msg = "a flash message should be returned for non-found users"
        # assert warning in str(res.data), err_msg

    @with_context
    def test_13_admin_user_add_del(self):
        """Test ADMIN add/del user to admin group works"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
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
        assert "Current Users with Admin privileges" in str(res.data)
        err_msg = "User.id=2 should be listed as an admin"
        assert "Juan Jose" in str(res.data), err_msg
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        assert "Current Users with Admin privileges" not in str(res.data)
        err_msg = "User.id=2 should be listed as an admin"
        assert "Juan Jose" not in str(res.data), err_msg
        # Delete a non existant user should return an error
        res = self.app.get("/admin/users/del/5000", follow_redirects=True)
        err = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert err['error'] == "User.id not found", err
        assert err['status_code'] == 404, err

    @with_context
    def test_13_admin_user_add_del_json(self):
        """Test ADMIN JSON add/del user to admin group works"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # Signin with admin user
        self.signin()
        # Add user.id=1000 (it does not exist)
        res = self.app_get_json("/admin/users/add/1000")
        err = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert err['error'] == "User not found", err
        assert err['status_code'] == 404, err

        # Add user.id=2 to admin group
        res = self.app_get_json("/admin/users/add/2")
        res = self.app_get_json("/admin/users")
        err_msg = "User.id=2 should be listed as an admin"
        data = json.loads(res.data)
        assert data['users'][0]['id'] == 2, data
        # Remove user.id=2 from admin group
        res = self.app_get_json("/admin/users/del/2", follow_redirects=True)
        res = self.app_get_json("/admin/users")
        data = json.loads(res.data)
        assert len(data['users']) == 0, data
        # Delete a non existant user should return an error
        res = self.app_get_json("/admin/users/del/5000")
        err = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert err['error'] == "User.id not found", err
        assert err['status_code'] == 404, err


    @with_context
    def test_14_admin_user_add_del_anonymous(self):
        """Test ADMIN add/del user to admin group works as anonymous"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        # Add user.id=2 to admin group
        res = self.app.get("/admin/users/add/2", follow_redirects=True)
        err_msg = "User should be redirected to signin"
        assert "Please sign in to access this page" in str(res.data), err_msg
        # Remove user.id=2 from admin group
        res = self.app.get("/admin/users/del/2", follow_redirects=True)
        err_msg = "User should be redirected to signin"
        assert "Please sign in to access this page" in str(res.data), err_msg

    @with_context
    def test_15_admin_user_add_del_authenticated(self):
        """Test ADMIN add/del user to admin group works as authenticated"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", name="juan2",
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
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signout()
        self.register(fullname="Juan Jose2", name="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin()
        # The user is redirected to '/admin/' if no format is specified
        res = self.app.get('/admin/users/export', follow_redirects=True)
        assert 'Featured Projects' in str(res.data), res.data
        assert 'Administrators' in str(res.data), res.data
        res = self.app.get('/admin/users/export?firmit=',
                           follow_redirects=True)
        assert 'Featured Projects' in str(res.data), res.data
        assert 'Administrators' in str(res.data), res.data
        # A 415 error is raised if the format is not supported (is not either
        # json or csv)
        res = self.app.get('/admin/users/export?format=bad',
                           follow_redirects=True)
        assert res.status_code == 415, res.status_code
        # JSON is a valid format for exports
        res = self.app.get('/admin/users/export?format=json',
                           follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'application/json', res.mimetype
        # CSV is a valid format for exports
        res = self.app.get('/admin/users/export?format=csv',
                           follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'text/csv', res.mimetype

    @with_context
    def test_17_admin_user_export_anonymous(self):
        """Test ADMIN user list export works as anonymous user"""
        self.register()
        self.signout()

        # Whichever the args of the request are, the user is redirected to
        # login
        res = self.app.get('/admin/users/export', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        res = self.app.get('/admin/users/export?firmit=',
                           follow_redirects=True)
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
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")

        # No matter what params in the request, Forbidden is raised
        res = self.app.get('/admin/users/export', follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?firmit=',
                           follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?format=bad',
                           follow_redirects=True)
        assert res.status_code == 403, res.status_code
        res = self.app.get('/admin/users/export?format=json',
                           follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    @patch('pybossa.forms.validator.requests.get')
    def test_19_admin_update_app(self, Mock, Mock2, mock_webhook):
        """Test ADMIN can update a project that belongs to another user"""
        html_request = FakeRequest(json.dumps(self.pkg_json_not_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        mock_webhook.return_value = html_request
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.new_project()
        self.signout()
        # Sign in with the root user
        self.signin()
        res = self.app.get('/project/sampleapp/settings')
        err_msg = "Admin users should be able to get the settings page for any project"
        assert res.status == "200 OK", err_msg
        res = self.update_project(method="GET")
        assert "Update" in str(res.data),\
            "The project should be updated by admin users"
        res = self.update_project(new_name="Root",
                                  new_short_name="rootsampleapp")
        res = self.app.get('/project/rootsampleapp', follow_redirects=True)
        assert "Root" in str(res.data), "The app should be updated by admin users"

        app = db.session.query(Project)\
                .filter_by(short_name="rootsampleapp").first()
        juan = db.session.query(User).filter_by(name="juan").first()
        assert app.owner_id == juan.id, "Owner_id should be: %s" % juan.id
        assert app.owner_id != 1, "The owner should be not updated"
        res = self.update_project(short_name="rootsampleapp",
                                  new_short_name="sampleapp",
                                  new_long_description="New Long Desc")
        res = self.app.get('/project/sampleapp', follow_redirects=True)
        err_msg = "The long description should have been updated"
        assert "New Long Desc" in str(res.data), err_msg

    @with_context
    @patch('pybossa.core.uploader.upload_file', return_value=True)
    def test_20_admin_delete_app(self, mock):
        """Test ADMIN can delete a project that belongs to another user"""
        self.register()
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.new_project()
        self.signout()
        # Sign in with the root user
        self.signin()
        res = self.delete_project(method="GET")
        assert "Yes, delete it" in str(res.data),\
            "The project should be deleted by admin users"
        res = self.delete_project()
        err_msg = "The project should be deleted by admin users"
        assert "Project deleted!" in str(res.data), err_msg

    @with_context
    def test_21_admin_delete_tasks(self):
        """Test ADMIN can delete a project's tasks that belongs to another user"""
        # Admin
        self.create()
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        assert len(tasks) > 0, "len(app.tasks) > 0"
        res = self.signin(email='root@root.com', password='tester' + 'root')
        res = self.app.get('/project/test-app/tasks/delete',
                           follow_redirects=True)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app.post('/project/test-app/tasks/delete',
                            follow_redirects=True)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg
        tasks = db.session.query(Task).filter_by(project_id=1).all()
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
    def test_22_admin_list_categories_json(self):
        """Test ADMIN JSON list categories works"""
        self.create()
        # Anonymous user
        url = '/admin/categories'
        res = self.app_get_json(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        self.signout()

        # Admin user
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "Admin users should be get a list of Categories"
        assert data.get('categories') is not None, err_msg
        assert data.get('template') == 'admin/categories.html', err_msg
        assert data.get('form') is not None, err_msg
        assert data.get('form').get('csrf') is not None, err_msg
        assert data.get('n_projects_per_category') is not None, err_msg
        assert data.get('n_projects_per_category').get('thinking') == 1, err_msg


    @with_context
    def test_23_admin_add_category(self):
        """Test ADMIN add category works"""
        self.create()
        category = {'name': 'cat', 'short_name': 'cat',
                    'description': 'description', 'id': ""}
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
        assert "Category added" in str(res.data), err_msg
        assert category['name'] in str(res.data), err_msg

        # Create the same category again should fail
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category form validation should work"
        assert "Please correct the errors" in str(res.data), err_msg

    @with_context
    def test_23_admin_add_category_json(self):
        """Test ADMIN JSON add category works"""
        self.create()
        category = {'name': 'cat', 'short_name': 'cat',
                    'description': 'description', 'id': ""}
        # Anonymous user
        url = '/admin/categories'
        res = self.app_post_json(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app_post_json(url, data=category, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        data = json.loads(res.data)
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        self.signout()

        # Admin
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app_post_json(url, data=category)
        err_msg = "Category should be added"
        data = json.loads(res.data)
        assert "Category added" in data.get('flash'), err_msg
        assert data.get('status') == 'success', err_msg
        assert category['name'] in list(data.get('n_projects_per_category').keys()), err_msg

        # Create the same category again should fail
        res = self.app_post_json(url, data=category)
        err_msg = "Category form validation should work"
        data = json.loads(res.data)
        assert "Please correct the errors" in data.get('flash'), err_msg
        assert data.get('status') == 'error', err_msg
        assert len(data.get('form').get('errors').get('name')) == 1, err_msg

    @with_context
    def test_24_admin_update_category_json(self):
        """Test ADMIN JSON update category works"""
        self.create()
        obj = db.session.query(Category).get(1)
        _name = obj.name
        category = obj.dictize()

        # Anonymous user GET
        url = '/admin/categories/update/%s' % obj.id
        res = self.app_get_json(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        # Anonymous user POST
        res = self.app_post_json(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin GET
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app_post_json(url, follow_redirects=True)
        data = json.loads(res.data)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        # Authenticated user but not admin POST
        res = self.app_post_json(url, data=category, follow_redirects=True)
        err_msg = "Non-Admin users should get 403"
        data = json.loads(res.data)
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        self.signout()

        # Admin GET
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "Category should be listed for admin user"
        assert data.get('category').get('name') == _name, err_msg
        assert data.get('form') is not None, data
        assert data.get('form').get('csrf') is not None, data
        # Check 404
        url_404 = '/admin/categories/update/5000'
        res = self.app_get_json(url_404, follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert data.get('code') == 404, data
        # Admin POST
        res = self.app_post_json(url, data=category)
        err_msg = "Category should be updated"
        data = json.loads(res.data)
        assert "Category updated" in data.get('flash'), err_msg
        assert data.get('status') == 'success', err_msg
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert category['name'] == data.get('category').get('name'), err_msg
        updated_category = db.session.query(Category).get(obj.id)
        assert updated_category.name == obj.name, err_msg
        # With not valid form
        category['name'] = None
        res = self.app_post_json(url, data=category)
        data = json.loads(res.data)
        assert "Please correct the errors" in data.get('flash'), err_msg
        assert data.get('form').get('errors') is not None, data
        assert len(data.get('form').get('errors').get('name')) ==1, data


    @with_context
    def test_24_admin_update_category(self):
        """Test ADMIN update category works"""
        self.create()
        obj = db.session.query(Category).get(1)
        _name = obj.name
        category = obj.dictize()
        del category['info']

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
        assert _name in str(res.data), err_msg
        # Check 404
        url_404 = '/admin/categories/update/5000'
        res = self.app.get(url_404, follow_redirects=True)
        assert res.status_code == 404, res.status_code
        # Admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category should be updated"
        assert "Category updated" in str(res.data), err_msg
        assert category['name'] in str(res.data), err_msg
        updated_category = db.session.query(Category).get(obj.id)
        assert updated_category.name == obj.name, err_msg
        # With not valid form
        category['name'] = None
        res = self.app.post(url, data=category, follow_redirects=True)
        assert "Please correct the errors" in str(res.data), err_msg

    @with_context
    def test_25_admin_delete_category_json(self):
        """Test ADMIN JSON delete category works"""
        self.create()
        obj = db.session.query(Category).get(2)
        category = obj.dictize()

        # Anonymous user GET
        url = '/admin/categories/del/%s' % obj.id
        res = self.app_get_json(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg
        # Anonymous user POST
        res = self.app_post_json(url, data=category, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous users should be redirected to sign in"
        assert dom.find(id='signin') is not None, err_msg

        # Authenticated user but not admin GET
        self.signin(email=self.email_addr2, password=self.password)
        res = self.app_post_json(url, follow_redirects=True)
        data = json.loads(res.data)
        err_msg = "Non-Admin users should get 403"
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        # Authenticated user but not admin POST
        res = self.app_post_json(url, data=category)
        err_msg = "Non-Admin users should get 403"
        data = json.loads(res.data)
        assert res.status_code == 403, err_msg
        assert data.get('code') == 403, err_msg
        self.signout()

        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert data.get('form') is not None, data
        assert data.get('form').get('csrf') is not None, data
        assert data.get('category') is not None, data
        assert data.get('category').get('id') == category['id'], data
        # Admin POST
        res = self.app_post_json(url, data=category)
        data = json.loads(res.data)
        err_msg = "Category should be deleted"
        assert "Category deleted" in data.get('flash'), (err_msg, data)
        assert data.get('status') == 'success', err_msg
        output = db.session.query(Category).get(obj.id)
        assert output is None, err_msg
        # Non existant category
        category['id'] = 5000
        url = '/admin/categories/del/5000'
        res = self.app_post_json(url, data=category)
        data = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert data.get('code') == 404, data

        # Now try to delete the only available Category
        obj = db.session.query(Category).first()
        url = '/admin/categories/del/%s' % obj.id
        category = obj.dictize()
        res = self.app_post_json(url, data=category)
        print(res.data)
        data = json.loads(res.data)
        err_msg = "Category should not be deleted"
        assert "Sorry" in data.get('flash'), data
        assert data.get('status') == 'warning', data
        output = db.session.query(Category).get(obj.id)
        assert output.id == category['id'], err_msg


    @with_context
    def test_25_admin_delete_category(self):
        """Test ADMIN delete category works"""
        self.create()
        obj = db.session.query(Category).get(2)
        category = obj.dictize()
        del category['info']

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
        assert category['name'] in str(res.data), err_msg
        # Admin POST
        res = self.app.post(url, data=category, follow_redirects=True)
        err_msg = "Category should be deleted"
        assert "Category deleted" in str(res.data), err_msg
        assert category['name'] not in str(res.data), err_msg
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
        del category['info']
        res = self.app.post(url, data=category, follow_redirects=True)
        print(res.data)
        err_msg = "Category should not be deleted"
        assert "Category deleted" not in str(res.data), err_msg
        assert category['name'] in str(res.data), err_msg
        output = db.session.query(Category).get(obj.id)
        assert output.id == category['id'], err_msg

    @with_context
    def test_admin_dashboard(self):
        """Test ADMIN dashboard requires admin"""
        url = '/admin/dashboard/'
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should require login"
        assert "Sign in" in str(res.data), err_msg

    @with_context
    def test_admin_dashboard_json(self):
        """Test ADMIN JSON dashboard requires admin"""
        url = '/admin/dashboard/'
        res = self.app_get_json(url, follow_redirects=True)
        err_msg = "It should require login"
        assert "Sign in" in str(res.data), err_msg


    @with_context
    def test_admin_dashboard_auth_user(self):
        """Test ADMIN dashboard requires admin"""
        url = '/admin/dashboard/'
        self.register()
        self.signout()
        self.register(fullname="juan", name="juan")
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should return 403"
        assert res.status_code == 403, err_msg

    @with_context
    def test_admin_dashboard_auth_user_json(self):
        """Test ADMIN JSON dashboard requires admin"""
        url = '/admin/dashboard/'
        self.register()
        self.signout()
        self.register(fullname="juan", name="juan")
        res = self.app_get_json(url)
        err_msg = "It should return 403"
        assert res.status_code == 403, err_msg
        data = json.loads(res.data)
        assert data.get('code') == 403, err_msg


    @with_context
    def test_admin_dashboard_admin_user(self):
        """Test ADMIN dashboard admins can access it"""
        url = '/admin/dashboard/'
        self.register()
        self.new_project()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should return 200"
        assert res.status_code == 200, err_msg
        assert "No data" in str(res.data), res.data

    @with_context
    def test_admin_dashboard_admin_user_json(self):
        """Test ADMIN JSON dashboard admins can access it"""
        url = '/admin/dashboard/'
        self.register()
        self.new_project()
        res = self.app_get_json(url)
        print(res.data)
        err_msg = "It should return 200"
        data = json.loads(res.data)
        assert res.status_code == 200, err_msg
        assert data.get('wait') == True, data

    @with_context
    def test_admin_dashboard_admin_user_data_json(self):
        """Test ADMIN JSON dashboard admins can access it with data"""
        url = '/admin/dashboard/'
        self.register()
        self.new_project()
        self.new_task(1)
        import pybossa.dashboard.jobs as dashboard
        dashboard.active_anon_week()
        dashboard.active_users_week()
        dashboard.new_users_week()
        dashboard.new_tasks_week()
        dashboard.new_task_runs_week()
        dashboard.draft_projects_week()
        dashboard.published_projects_week()
        dashboard.update_projects_week()
        dashboard.returning_users_week()
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "It should return 200"
        assert res.status_code == 200, err_msg
        keys = ['active_anon_last_week', 'published_projects_last_week',
                'new_tasks_week', 'title', 'update_feed',
                'draft_projects_last_week', 'update_projects_last_week',
                'new_users_week', 'template', 'new_task_runs_week',
                'returning_users_week', 'active_users_last_week', 'wait']
        for key in keys:
            assert key in list(data.keys()), data


    @with_context
    def test_admin_dashboard_admin_user_data(self):
        """Test ADMIN dashboard admins can access it with data"""
        url = '/admin/dashboard/'
        self.register()
        self.new_project()
        self.new_task(1)
        import pybossa.dashboard.jobs as dashboard
        dashboard.active_anon_week()
        dashboard.active_users_week()
        dashboard.new_users_week()
        dashboard.new_tasks_week()
        dashboard.new_task_runs_week()
        dashboard.draft_projects_week()
        dashboard.published_projects_week()
        dashboard.update_projects_week()
        dashboard.returning_users_week()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should return 200"
        assert res.status_code == 200, err_msg
        assert "No data" not in str(res.data), res.data
        assert "New Users" in str(res.data), res.data

    @with_context
    @patch('pybossa.view.admin.DASHBOARD_QUEUE')
    def test_admin_dashboard_admin_refresh_user_data(self, mock):
        """Test ADMIN dashboard admins refresh can access it with data"""
        url = '/admin/dashboard/?refresh=1'
        self.register()
        self.new_project()
        self.new_task(1)
        import pybossa.dashboard.jobs as dashboard
        dashboard.active_anon_week()
        dashboard.active_users_week()
        dashboard.new_users_week()
        dashboard.new_tasks_week()
        dashboard.new_task_runs_week()
        dashboard.draft_projects_week()
        dashboard.published_projects_week()
        dashboard.update_projects_week()
        dashboard.returning_users_week()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should return 200"
        assert res.status_code == 200, err_msg
        assert "No data" not in str(res.data), res.data
        assert "New Users" in str(res.data), res.data
        assert mock.enqueue.called

    @with_context
    @patch('pybossa.view.admin.DASHBOARD_QUEUE')
    def test_admin_dashboard_admin_refresh_user_data_json(self, mock):
        """Test ADMIN JSON dashboard admins refresh can access it with data"""
        url = '/admin/dashboard/?refresh=1'
        self.register()
        self.new_project()
        self.new_task(1)
        import pybossa.dashboard.jobs as dashboard
        dashboard.active_anon_week()
        dashboard.active_users_week()
        dashboard.new_users_week()
        dashboard.new_tasks_week()
        dashboard.new_task_runs_week()
        dashboard.draft_projects_week()
        dashboard.published_projects_week()
        dashboard.update_projects_week()
        dashboard.returning_users_week()
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "It should return 200"
        assert res.status_code == 200, err_msg
        assert mock.enqueue.called
        keys = ['active_anon_last_week', 'published_projects_last_week',
                'new_tasks_week', 'title', 'update_feed',
                'draft_projects_last_week', 'update_projects_last_week',
                'new_users_week', 'template', 'new_task_runs_week',
                'returning_users_week', 'active_users_last_week', 'wait']
        for key in keys:
            assert key in list(data.keys()), data

    @with_context
    def test_announcement_json(self):
        """Test ADMIN JSON announcement"""
        url = '/admin/announcement'
        self.register()
        res = self.app_get_json(url)
        print(res.data)
        err_msg = "It should return 200"
        data = json.loads(res.data)
        assert res.status_code == 200, err_msg
        assert "announcements" in list(data.keys()), data
        assert "csrf" in list(data.keys()), data
        assert "template" in list(data.keys()), data
        assert "title" in list(data.keys()), data
        # create an announcement in DB
        announcement = AnnouncementFactory.create()
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert data['template'] == 'admin/announcement.html'
        announcement0 = data['announcements'][0]
        assert announcement0['body'] == 'Announcement body text'
        assert announcement0['title'] == 'Announcement title'
        assert announcement0['id'] == 1


    @with_context
    def test_announcement_create_json(self):
        """Test announcement creation"""
        self.register()
        user = user_repo.get(1)
        url = "/admin/announcement/new"

        res = self.app_get_json(url)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data['template'] == 'admin/new_announcement.html'

        csrf = self.get_csrf(url)
        headers = {'X-CSRFToken': csrf}
        res = self.app_post_json(url,
                                 data={'title':'announcement title', 'body':'body text'},
                                 headers=headers, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert 'created' in data['flash'], data
        assert data['next'] == '/admin/announcement', data
        assert data['status'] == 'success', data

        announcement = announcement_repo.get_by(title='announcement title')
        assert announcement.title == 'announcement title', announcement.title
        assert announcement.body == 'body text', announcement.body
        assert announcement.user_id == user.id, announcement.user_id

    @with_context
    def test_announcement_create_non_admin_json(self):
        self.register()
        self.signout()
        url = "/admin/announcement/new"

        res = self.app_get_json(url)
        assert res.status_code == 302, res.status_code

        res = self.app_post_json(url, data={'title':'blogpost title', 'body':'body'})
        assert res.status_code == 302, res.status_code

    @with_context
    def test_announcement_update_json(self):
        """Test announcement update"""
        self.register()
        user = user_repo.get(1)
        announcement = AnnouncementFactory.create()
        url = "/admin/announcement/1/update"

        res = self.app_get_json(url)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data['template'] == 'admin/new_announcement.html'

        res = self.app_get_json('/admin/announcement/2/update')
        assert res.status_code == 404, res.status_code

        csrf = self.get_csrf(url)
        headers = {'X-CSRFToken': csrf}
        res = self.app_post_json(url,
                                 data={'id': announcement.id,
                                       'title': 'updated title', 'body': 'updated body'},
                                 headers=headers, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert 'updated' in data['flash'], data
        assert data['next'] == '/admin/announcement', data
        assert data['status'] == 'success', data
        check_announcement = announcement_repo.get_by(id=announcement.id)
        assert check_announcement.title == 'updated title', announcement.title
        assert check_announcement.body == 'updated body', announcement.body
        assert check_announcement.user_id == user.id, announcement.user_id

    @with_context
    def test_announcement_update_json_error(self):
        """Test announcement update error"""
        self.register()
        user = user_repo.get(1)
        announcement = AnnouncementFactory.create()
        url = "/admin/announcement/1/update"

        res = self.app_get_json(url)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data['template'] == 'admin/new_announcement.html'

        res = self.app_get_json('/admin/announcement/2/update')
        assert res.status_code == 404, res.status_code

        csrf = self.get_csrf(url)
        headers = {'X-CSRFToken': csrf}
        res = self.app_post_json('/admin/announcement/2/update',
                                 data={'id': 2,
                                       'title': 'updated title', 'body': 'updated body'},
                                 headers=headers, follow_redirects=True)
        assert res.status_code == 404, res.status_code

    @with_context
    def test_announcement_delete_json(self):
        """Test announcement delete"""
        self.register()
        user = user_repo.get(1)
        print(user.admin)
        announcement = AnnouncementFactory.create()
        url = "/admin/announcement/1/delete"

        res = self.app_post_json(url)
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert 'deleted' in data['flash'], data
        assert data['next'] == '/admin/announcement'
        assert data['status'] == 'success'
        announcements = announcement_repo.get_all_announcements()
        assert len(announcements) == 0, announcements
