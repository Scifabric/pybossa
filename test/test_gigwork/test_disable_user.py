# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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

from default import db, Fixtures, with_context, with_context_settings, \
    FakeResponse, mock_contributions_guard
from helper import web
from pybossa.core import user_repo
from helper.gig_helper import make_subadmin_by


class TestWeb(web.Helper):

    @with_context
    def test_disable_user(self):
        """Test disable enable user works"""
        self.register()
        self.signin()
        self.register(name='tyrion')
        user = user_repo.get_by_name('tyrion')
        self.app.get('/admin/users/disable_user/{}'.format(user.id))
        self.signout()
        res = self.signin(email='tyrion@example.com')
        assert 'Your account is disabled. ' in res.data, res.data

        self.signin()
        self.app.get('/admin/users/enable_user/{}'.format(user.id))
        self.signout()
        res = self.signin(email='tyrion@example.com')
        assert 'Welcome back ' in res.data, res.data

    @with_context
    def test_disable_user_does_not_exist(self):
        """Test disable non existing user returns 404"""
        self.register()
        self.signin()
        res = self.app.get('/admin/users/disable_user/3')
        assert res.status_code == 404, res.status

        self.app.get('/admin/users/enable_user/3')
        assert res.status_code == 404, res.status

    @with_context
    def test_subadmin_cannot_disable_admin(self):
        """Test subadmin cannot disable admin user"""
        self.register(name='tyrion')
        self.signin()
        self.register(name='tywin')
        self.signout()
        make_subadmin_by(name='tywin')

        self.signin(email='tywin@example.com')
        tyrion = user_repo.get_by_name('tyrion')

        res = self.app.get('/admin/users/disable_user/{}'.format(tyrion.id))
        assert res.status_code == 403, res.status

        res = self.app.get('/admin/users/enable_user/{}'.format(tyrion.id))
        assert res.status_code == 403, res.status

    @with_context
    def test_user_cannot_disable_users(self):
        """Test user cannot disable users"""
        self.register()
        self.signin()
        self.register(name='tyrion')
        self.register(name='tywin')
        self.signout()

        self.signin(email='tyrion@example.com')
        tyrion = user_repo.get_by_name('tyrion')

        res = self.app.get('/admin/users/disable_user/{}'.format(tyrion.id))
        assert res.status_code == 403, res.status

        res = self.app.get('/admin/users/enable_user/{}'.format(tyrion.id))
        assert res.status_code == 403, res.status

    @with_context
    def test_subadmin_can_disable_users(self):
        """Test subadmin can disable users"""
        self.register()
        self.signin()
        self.register(name='tyrion')
        self.register(name='tywin')
        self.signout()

        make_subadmin_by(name='tyrion')
        self.signin(email='tyrion@example.com')
        tywin = user_repo.get_by_name('tywin')

        res = self.app.get('/admin/users/disable_user/{}'.format(tywin.id),
                           follow_redirects=True)
        assert res.status_code == 200, res.status

        res = self.app.get('/admin/users/enable_user/{}'.format(tywin.id),
                           follow_redirects=True)
        assert res.status_code == 200, res.status

    @with_context
    def test_enable_changes_last_login(self):
        """Test enabling user changes last login"""
        self.register()
        self.signin()
        self.register(name='tyrion')
        self.signout()

        self.signin(email='tyrion@example.com')
        user = user_repo.get_by_name('tyrion')
        last_login = user.last_login
        self.signout()

        self.signin()
        self.app.get('/admin/users/disable_user/{}'.format(user.id))

        self.app.get('/admin/users/enable_user/{}'.format(user.id))
        self.signout()

        user = user_repo.get_by_name('tyrion')
        assert user.last_login != last_login
