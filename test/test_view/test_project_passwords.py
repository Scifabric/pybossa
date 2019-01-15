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

from default import Test, db, with_context
from factories import ProjectFactory, TaskFactory, UserFactory, BlogpostFactory
from mock import patch

from pybossa.repositories import ProjectRepository
project_repo = ProjectRepository(db)


def configure_mock_current_user_from(user, mock):
    mock.is_anonymous = False
    mock.is_authenticated = True
    mock.admin = user.admin if user != None else None
    mock.id = user.id if user != None else None
    return mock


class TestProjectPassword(Test):


    from pybossa.view.projects import redirect
    @with_context
    @patch('pybossa.view.projects.redirect', wraps=redirect)
    def test_password_view_func_post(self, redirect):
        """Test when posting to /project/short_name/password and password is correct
        the user is redirected to where they came from"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)
        redirect_url = '/project/%s/task/%s' % (project.short_name, task.id)
        url = '/project/%s/password?next=%s' % (project.short_name, redirect_url)

        res = self.app.post(url, data={'password': 'mysecret'})
        redirect.assert_called_with(redirect_url)

    @with_context
    def test_password_view_func_post_wrong_passwd(self):
        """Test when posting to /project/short_name/password and password is incorrect
        an error message is flashed"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)
        url = '/project/%s/password?next=/project/%s/task/%s' % (
            project.short_name, project.short_name, task.id)

        res = self.app.post(url, data={'password': 'bad_passwd'})
        assert 'Sorry, incorrect password' in str(res.data), "No error message shown"

    @with_context
    def test_password_view_func_no_project(self):
        """Test when receiving a request to a non-existing project, return 404"""
        get_res = self.app.get('/project/noapp/password')
        post_res = self.app.post('/project/noapp/password')

        assert get_res.status_code == 404, get_res.status_code
        assert post_res.status_code == 404, post_res.status_code

    @with_context
    def test_password_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a password
        protected project is redirected to the password view"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in str(res.data)

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in str(res.data)

    @with_context
    def test_password_not_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

    @with_context
    @patch('pybossa.password_manager.current_user')
    def test_password_required_for_authenticated_contributors(self, mock_user):
        """Test when an authenticated user wants to contribute to a password
        protected project is redirected to the password view"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in str(res.data)

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in str(res.data)

    @with_context
    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_authenticated_contributors(self, mock_user):
        """Test when an authenticated user wants to contribute to a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

    @with_context
    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_admins(self, mock_user):
        """Test when an admin wants to contribute to a password
        protected project is able to do it"""
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)
        mock_user.is_authenticated = True
        mock_user.is_anonymous = False
        assert mock_user.admin
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data), res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

    @with_context
    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_owner(self, mock_user):
        """Test when the owner wants to contribute to a password
        protected project is able to do it"""
        owner = UserFactory.create_batch(2)[1]
        configure_mock_current_user_from(owner, mock_user)
        assert owner.admin is False
        project = ProjectFactory.create(owner=owner)
        assert project.owner.id == owner.id
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data), res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in str(res.data)

    @with_context
    def test_endpoints_with_password_protection(self):
        """Test all the endpoints for "reading" a project use password protection """
        endpoints_requiring_password = (
            '/', '/tutorial', '/1/results.json',
            '/tasks/', '/tasks/browse', '/tasks/export',
            '/stats', '/blog', '/1', '/task/1')
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        BlogpostFactory.create(project=project, published=True)
        project.set_password('mysecret')
        project_repo.update(project)

        for endpoint in endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' in str(res.data), endpoint

    @with_context
    @patch('pybossa.view.projects.ensure_authorized_to')
    def test_password_protection_overrides_normal_auth(self, fake_authorizer):
        """Test if a project is password protected, that is the only authorization
        required for it to be seen"""
        project = ProjectFactory.create(published=False)
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        self.app.get('/project/%s' % project.short_name, follow_redirects=True)

        assert fake_authorizer.called == False

    @with_context
    @patch('pybossa.view.projects.ensure_authorized_to')
    def test_normal_auth_used_if_no_password_protected(self, fake_authorizer):
        """Test if a project is password protected, that is the only authorization
        required for it to be seen"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)

        self.app.get('/project/%s' % project.short_name, follow_redirects=True)

        assert fake_authorizer.called == True

    @with_context
    def test_get_reset_project_secret_key(self):
        """Test GET project reset key method works."""
        project = ProjectFactory.create()
        url = '/project/%s/resetsecretkey' % project.short_name
        res = self.app.get(url)
        assert res.status_code == 405, res.status_code

    @with_context
    def test_reset_project_secret_key(self):
        """Test project reset key method works."""
        project = ProjectFactory.create()
        url = '/project/%s/resetsecretkey' % project.short_name
        res = self.app.post(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        err_msg = "User should be redirected to sign in."
        assert "Sign in" in str(res.data), err_msg
