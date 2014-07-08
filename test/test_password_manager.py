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

from pybossa.cookies import CookieHandler
from pybossa.password_manager import ProjectPasswdManager

from mock import patch, MagicMock



class TestProjectPasswdManager(object):
    """Unit tests for class ProjectPasswdManager methods"""

    def setUp(self):
        self.cookie_handler = MagicMock()
        self.psswd_mngr = ProjectPasswdManager(self.cookie_handler)
        self.project = MagicMock()

    def tearDown(self):
        self.cookie_handler = None
        self.psswd_mngr = None
        self.project = None


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_anon_passwd_no_ip(self, mock_user):
        """Test password_needed should return True for an anonymous user and
        a project with password, if the cookie does not contain the user IP"""
        mock_user.is_anonymous.return_value = True
        mock_user.admin = False
        self.cookie_handler.get_cookie_from.return_value = []
        self.project.needs_password.return_value = True
        user_ip = '127.0.0.1'

        password_needed = self.psswd_mngr.password_needed(self.project, user_ip)

        self.cookie_handler.get_cookie_from.assert_called_with(self.project)
        assert password_needed is True, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_anon_passwd_ip(self, mock_user):
        """Test password_needed should return False for an anonymous user and
        a project with password, if the cookie contains the user IP"""
        mock_user.is_anonymous.return_value = True
        mock_user.admin = False
        self.cookie_handler.get_cookie_from.return_value = ['127.0.0.1']
        self.project.needs_password.return_value = True
        user_ip = '127.0.0.1'

        password_needed = self.psswd_mngr.password_needed(self.project, user_ip)

        self.cookie_handler.get_cookie_from.assert_called_with(self.project)
        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_anon_no_passwd(self, mock_user):
        """Test password_needed should return False for an anonymous user and
        a project without password"""
        mock_user.is_anonymous.return_value = True
        mock_user.admin = False
        self.project.needs_password.return_value = False
        user_ip = '127.0.0.1'

        password_needed = self.psswd_mngr.password_needed(self.project, user_ip)

        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_auth_passwd_no_id(self, mock_user):
        """Test password_needed should return True for an authenticated user and
        a project with password, if the cookie does not contain the user id"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = False
        mock_user.id = 2
        self.cookie_handler.get_cookie_from.return_value = []
        self.project.needs_password.return_value = True

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        self.cookie_handler.get_cookie_from.assert_called_with(self.project)
        assert password_needed is True, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_auth_passwd_ip(self, mock_user):
        """Test password_needed should return False for an authenticated user and
        a project with password, if the cookie contains the user id"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = False
        mock_user.id = 2
        self.cookie_handler.get_cookie_from.return_value = [2]
        self.project.needs_password.return_value = True

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        self.cookie_handler.get_cookie_from.assert_called_with(self.project)
        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_auth_no_passwd(self, mock_user):
        """Test password_needed should return False for an authenticated user and
        a project without password"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = False
        mock_user.id = 2
        self.project.needs_password.return_value = False

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_owner_no_passwd(self, mock_user):
        """Test password_needed returns False for project owner if it has no
        password"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = False
        mock_user.id = 2
        self.project.needs_password.return_value = False
        self.project.owner_id = 2

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_owner_no_passwd(self, mock_user):
        """Test password_needed returns False for project owner even it has a
        password"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = False
        mock_user.id = 2
        self.project.needs_password.return_value = True
        self.project.owner_id = 2

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_admin_no_passwd(self, mock_user):
        """Test password_needed returns False for admins if project has no
        password"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = True
        mock_user.id = 1
        self.project.needs_password.return_value = False
        self.project.owner_id = 2

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        assert password_needed is False, password_needed


    @patch('pybossa.password_manager.current_user')
    def test_password_needed_owner_no_passwd(self, mock_user):
        """Test password_needed returns False for project owner even project has
        a password"""
        mock_user.is_anonymous.return_value = False
        mock_user.admin = True
        mock_user.id = 1
        self.project.needs_password.return_value = True
        self.project.owner_id = 2

        password_needed = self.psswd_mngr.password_needed(self.project, mock_user.id)

        assert password_needed is False, password_needed
