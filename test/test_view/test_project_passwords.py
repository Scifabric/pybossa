# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from default import Test, db, with_context
from factories import ProjectFactory, TaskFactory, UserFactory
from mock import patch

from pybossa.repositories import ProjectRepository
project_repo = ProjectRepository(db)


def configure_mock_current_user_from(user, mock):
    def is_anonymous():
        return user is None
    mock.is_anonymous.return_value = is_anonymous()
    mock.admin = user.admin if user != None else None
    mock.id = user.id if user != None else None
    return mock


class TestProjectPassword(Test):


    from pybossa.view.projects import redirect
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
        assert 'Sorry, incorrect password' in res.data, "No error message shown"


    def test_password_view_func_no_project(self):
        """Test when receiving a request to a non-existing project, return 404"""
        get_res = self.app.get('/project/noapp/password')
        post_res = self.app.post('/project/noapp/password')

        assert get_res.status_code == 404, get_res.status_code
        assert post_res.status_code == 404, post_res.status_code


    def test_password_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a password
        protected project is redirected to the password view"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data


    def test_password_not_required_for_anonymous_contributors(self):
        """Test when an anonymous user wants to contribute to a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


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
        assert 'Enter the password to contribute' in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' in res.data


    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_authenticated_contributors(self, mock_user):
        """Test when an authenticated user wants to contribute to a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_admins(self, mock_user):
        """Test when an admin wants to contribute to a password
        protected project is able to do it"""
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)
        assert mock_user.admin
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        res = self.app.get('/project/%s/newtask' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


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
        assert 'Enter the password to contribute' not in res.data

        res = self.app.get('/project/%s/task/1' % project.short_name, follow_redirects=True)
        assert 'Enter the password to contribute' not in res.data


    endpoints_requiring_password = ('/', '/tutorial', '/1/results.json',
                                    '/tasks/', '/tasks/browse', '/tasks/export',
                                    '/stats', '/blog')


    def test_password_required_for_anonymous_users_to_see_project(self):
        """Test when an anonymous user wants to visit a password
        protected project is redirected to the password view"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' in res.data, endpoint



    def test_password_not_required_for_anonymous_users_to_see_project(self):
        """Test when an anonymous user wants to visit a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' not in res.data, endpoint


    @patch('pybossa.password_manager.current_user')
    def test_password_required_for_authenticated_users_to_see_project(self, mock_user):
        """Test when an authenticated user wants to visit a password
        protected project is redirected to the password view"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' in res.data, endpoint


    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_authenticated_users_to_see_project(self, mock_user):
        """Test when an authenticated user wants to visit a non-password
        protected project is able to do it"""
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' not in res.data, endpoint


    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_admins_to_see_project(self, mock_user):
        """Test when an admin wants to visit a password
        protected project is able to do it"""
        user = UserFactory.create()
        configure_mock_current_user_from(user, mock_user)
        assert mock_user.admin
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' not in res.data, endpoint


    @patch('pybossa.password_manager.current_user')
    def test_password_not_required_for_owner_to_see_project(self, mock_user):
        """Test when the owner wants to visit a password
        protected project is able to do it"""
        owner = UserFactory.create_batch(2)[1]
        configure_mock_current_user_from(owner, mock_user)
        assert owner.admin is False
        project = ProjectFactory.create(owner=owner)
        assert project.owner.id == owner.id
        TaskFactory.create(project=project)
        project.set_password('mysecret')
        project_repo.update(project)

        for endpoint in self.endpoints_requiring_password:
            res = self.app.get('/project/%s%s' % (project.short_name, endpoint),
                               follow_redirects=True)
            assert 'Enter the password to contribute' not in res.data, endpoint
