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

from default import Test, db
from factories import AppFactory, TaskFactory, UserFactory
from factories import reset_all_pk_sequences
from mock import patch



def configure_mock_current_user_from(user, mock):
    def is_anonymous():
        return user is None
    mock.is_anonymous.return_value = is_anonymous()
    mock.admin = user.admin if user != None else None
    mock.id = user.id if user != None else None
    return mock


class TestProjectPassword(Test):

    def setUp(self):
        super(TestProjectPassword, self).setUp()
        reset_all_pk_sequences()


    def test_password_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a password
        protected project is redirected to the password view"""
        app = AppFactory.create()
        TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data


    def test_password_not_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a non-password
        protected project is able to do it"""
        app = AppFactory.create()
        TaskFactory.create(app=app)

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    @patch('pybossa.view.applications.current_user')
    def test_password_required_for_authenticated_contributors(self, mock_user):
        """Test when an authenticated user wants to contribute to a password
        protected project is redirected to the password view"""
        app = AppFactory.create()
        TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data


    @patch('pybossa.view.applications.current_user')
    def test_password_not_required_for_authenticated_contributors(self, mock_user):
        """Test when an authenticated user wants to contribute to a non-password
        protected project is able to do it"""
        app = AppFactory.create()
        TaskFactory.create(app=app)
        db.session.add(app)
        db.session.commit()
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    @patch('pybossa.view.applications.current_user')
    def test_password_not_required_for_admins(self, mock_user):
        """Test when an admin wants to contribute to a password
        protected project is able to do it"""
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)
        assert mock_user.admin
        app = AppFactory.create()
        TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    @patch('pybossa.view.applications.current_user')
    def test_password_not_required_for_owner(self, mock_user):
        """Test when the owner wants to contribute to a password
        protected project is able to do it"""
        owner = UserFactory.create_batch(2)[1]
        configure_mock_current_user_from(owner, mock_user)
        assert owner.admin is False
        app = AppFactory.create(owner=owner)
        assert app.owner.id == owner.id
        TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()

        res = self.app.get('/app/%s/newtask' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/app/%s/task/1' % app.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    from pybossa.view.applications import redirect
    @patch('pybossa.view.applications.redirect', wraps=redirect)
    def test_password_view_func_post(self, redirect):
        """Test when posting to /app/short_name/password and password is correct
        the user is redirected to where they came from"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()
        user = UserFactory.create()
        redirect_url = '/app/%s/task/%s' % (app.short_name, task.id)
        url = '/app/%s/password?next=%s' % (app.short_name, redirect_url)

        res = self.app.post(url, data={'password': 'mysecret'})
        redirect.assert_called_with(redirect_url)


    def test_password_view_func_post_wrong_passwd(self):
        """Test when posting to /app/short_name/password and password is incorrect
        an error message is flashed"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)
        app.set_password('mysecret')
        db.session.add(app)
        db.session.commit()
        user = UserFactory.create()
        url = '/app/%s/password?next=/app/%s/task/%s' % (app.short_name, app.short_name, task.id)

        res = self.app.post(url, data={'password': 'bad_passwd'})
        assert 'Sorry, incorrect password' in res.data, "No error message shown"


    def test_password_view_func_no_project(self):
        """Test when receiving a request to a non-existing app, return 404"""
        get_res = self.app.get('/app/noapp/password')
        post_res = self.app.post('/app/noapp/password')

        assert get_res.status_code == 404, get_res.status_code
        assert post_res.status_code == 404, post_res.status_code
